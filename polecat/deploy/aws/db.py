from coolname import generate_slug
from psycopg2.sql import SQL, Identifier
from termcolor import colored

from ...db.connection import cursor
from ...utils import random_ident
from ...utils.feedback import feedback
from .constants import DEPLOYMENT_PREFIX
from .exceptions import KnownError
from .operations import (delete_parameter, get_parameter,
                         get_parameters_by_path, set_parameter)
from .secret import create_secret
from .utils import aws_client


def get_db_name(project, deployment):
    return f'{project.lower()}_{deployment.lower()}'


def get_rds_instance(instance_id, rds=None):
    rds = aws_client('rds')
    response = rds.describe_db_instances(
        Filters=[{
            'Name': 'db-instance-id',
            'Values': [instance_id]
        }]
    )
    return response['DBInstances'][0]


def get_db_url(username, password, address, db_name):
    return f'postgres://{username}:{password}@{address}/{db_name}'


def get_db_url_components(url):
    # TODO: Fix
    return {
        'address': url[url.find('@') + 1:url.rfind('/')],
        'db_name': url[url.rfind('/'):]
    }


def replace_db_name(url, db_name):
    return url[:url.rfind('/') + 1] + db_name


@feedback
def create_instance(url=None, instance_class='db.t2.micro',
                    storage=10, master_username='master', backup_days=0,
                    feedback=None):
    rds = aws_client('rds')
    instance_name = generate_slug(2)
    password = random_ident(36)
    action = 'Use' if url else 'Provision'
    with feedback(f'{action} database instance {colored(instance_name, "blue")}'):
        if not url:
            rds.create_db_instance(
                DBName='master',
                DBInstanceIdentifier=instance_name,
                DBInstanceClass='db.t2.micro',
                Engine='postgres',
                AllocatedStorage=storage,
                StorageType='gp2',
                MasterUsername=master_username,
                MasterUserPassword=password,
                BackupRetentionPeriod=backup_days,
                PubliclyAccessible=True,
                Tags=[{
                    'Key': 'Builder',
                    'Value': 'Polecat'
                }]
            )
            waiter = rds.get_waiter('db_instance_available')
            waiter.wait(DBInstanceIdentifier=instance_name)
            address = get_rds_instance(instance_name)['Endpoint']['Address']
            url = get_db_url('master', password, address, 'master')
        set_parameter(
            f'/polecat/aws/db/instances/{instance_name}/url',
            url
        )
    return instance_name, url


@feedback
def delete_instance(name, feedback=None):
    rds = aws_client('rds')
    with feedback(f'Delete database instance {colored(name, "blue")}'):
        databases = get_parameters_by_path(
            f'/polecat/aws/db/instances/{name}/databases/'
        )
        if databases:
            raise KnownError('instance not empty')
        rds.delete_db_instance(
            DBInstanceIdentifier=name,
            DeleteAutomatedBackups=True,
            SkipFinalSnapshot=True
        )
        waiter = rds.get_waiter('db_instance_deleted')
        waiter.wait(DBInstanceIdentifier=name)
        delete_parameter(
            f'/polecat/aws/db/instances/{name}/url'
        )


def list_instances(feedback=None):
    with feedback('Fetch instances') as fb:
        instances = get_parameters_by_path(f'/polecat/aws/db/instances/')
    return instances.keys()


@feedback
def create_db(project, deployment, instance_name=None, instance_class='db.t2.micro',
              storage=10, master_username='master', backup_days=0,
              feedback=None):
    if not instance_name:
        instance_name, instance_url = create_instance(
            instance_class=instance_class,
            storage=storage,
            master_username=master_username,
            backup_days=backup_days,
            feedback=feedback
        )
    else:
        instance_url = get_parameter(f'/polecat/aws/db/instances/{instance_name}/url')
    address = get_db_url_components(instance_url)['address']
    with feedback(f'Create database for {colored(project, "blue")}/{colored(deployment, "green")}'):
        db_name = get_db_name(project, deployment)
        password = random_ident(36)
        url = get_db_url(db_name, password, address, db_name)
        with cursor(instance_url) as curs:
            curs.execute(
                SQL('CREATE USER {} WITH CREATEROLE PASSWORD \'%s\'' % password).format(
                    Identifier(db_name)
                )
            )
            curs.execute(
                SQL('GRANT {} TO {}').format(
                    Identifier(db_name),
                    Identifier('master')
                )
            )
            curs.execute(
                SQL('CREATE DATABASE {db_name} WITH OWNER {db_name};').format(
                    db_name=Identifier(db_name)
                )
            )
            curs.execute(
                SQL('GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_name};').format(
                    db_name=Identifier(db_name)
                )
            )
        with cursor(replace_db_name(instance_url, db_name)) as curs:
            # TODO: Allow specification of other extensions.
            curs.execute((
                'CREATE EXTENSION IF NOT EXISTS chkpass;'
                'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
            ))
        set_parameter(
            f'/polecat/aws/db/instances/{instance_name}/databases/{db_name}/url',
            url
        )
        set_parameter(
            DEPLOYMENT_PREFIX.format(project, deployment) + f'databases/{db_name}/url',
            url
        )
        set_parameter(
            DEPLOYMENT_PREFIX.format(project, deployment) + f'databases/{db_name}/instance_name',
            instance_name
        )
    create_secret(
        project,
        deployment,
        'DATABASE_URL',
        url,
        feedback=feedback
    )


@feedback
def list_dbs(project, deployment, feedback=None):
    with feedback(f'List databases for {colored(project, "blue")}/{colored(deployment, "green")}'):
        dbs = get_parameters_by_path(
            DEPLOYMENT_PREFIX.format(project, deployment) + 'databases/'
        )
    return dbs.keys()


@feedback
def delete_db(project, deployment, feedback=None):
    db_name = get_db_name(project, deployment)
    with feedback(f'Delete database for {colored(project, "blue")}/{colored(deployment, "green")}'):
        info = get_parameters_by_path(
            DEPLOYMENT_PREFIX.format(project, deployment) + f'databases/{db_name}/',
        )
        instance_name = info['instance_name']
        instance_url = get_parameter(
            f'/polecat/aws/db/instances/{info["instance_name"]}/url'
        )
        with cursor(instance_url) as curs:
            curs.execute('''
              SELECT pg_terminate_backend(pg_stat_activity.pid)
              FROM pg_stat_activity
              WHERE pg_stat_activity.datname = '{}'
                AND pid <> pg_backend_pid();
            '''.format(db_name))
            curs.execute(SQL('DROP DATABASE {}').format(Identifier(db_name)))
            curs.execute(SQL('DROP USER {}').format(Identifier(db_name)))
        delete_parameter([
            f'/polecat/aws/db/instances/{instance_name}/databases/{db_name}/url',
            DEPLOYMENT_PREFIX.format(project, deployment) + f'databases/{db_name}/url',
            DEPLOYMENT_PREFIX.format(project, deployment) + f'databases/{db_name}/instance_name'
        ])
