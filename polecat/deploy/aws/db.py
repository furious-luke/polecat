from termcolor import colored

from ...utils import capitalize, random_ident
from ...utils.feedback import feedback
from .utils import aws_client
from .secret import create_secret


def get_instance_name(project, deployment):
    return f'{project}{capitalize(deployment)}'


def get_db_instance(instance_id, rds=None):
    rds = aws_client('rds')
    response = rds.describe_db_instances(
        Filters=[{
            'Name': 'db-instance-id',
            'Values': [instance_id]
        }]
    )
    return response['DBInstances'][0]


@feedback
def create_db(project, deployment, instance_class='db.t2.micro', storage=10,
              master_username='master', backup_days=0, feedback=None):
    rds = aws_client('rds')
    instance_name = get_instance_name(project, deployment)
    master_password = random_ident(36)
    with feedback(f'Provision database for {colored(project, "blue")}/{colored(deployment, "green")}'):
        rds.create_db_instance(
            DBName=instance_name,
            DBInstanceIdentifier=instance_name,
            DBInstanceClass='db.t2.micro',
            Engine='postgres',
            AllocatedStorage=storage,
            StorageType='gp2',
            MasterUsername=master_username,
            MasterUserPassword=master_password,
            BackupRetentionPeriod=backup_days,
            PubliclyAccessible=True,
            Tags=[{
                'Key': 'Builder',
                'Value': 'Polecat'
            }, {
                'Key': 'PolecatProject',
                'Value': project,
            }, {
                'Key': 'PolecatDeployment',
                'Value': deployment
            }]
        )
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=instance_name)
        address = get_db_instance(instance_name)['Endpoint']['Address']
    create_secret(
        project,
        deployment,
        'DATABASE_URL',
        f'postgres://master:{master_password}@{address}/{instance_name}',
        feedback=feedback
    )


@feedback
def delete_db(project, deployment, feedback=None):
    rds = aws_client('rds')
    instance_name = get_instance_name(project, deployment)
    with feedback(f'Delete database for {colored(project, "blue")}/{colored(deployment, "green")}'):
        rds.delete_db_instance(
            DBInstanceIdentifier=instance_name,
            DeleteAutomatedBackups=True,
            SkipFinalSnapshot=True
        )
        waiter = rds.get_waiter('db_instance_deleted')
        waiter.wait(DBInstanceIdentifier=instance_name)
