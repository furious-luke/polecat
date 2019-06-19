import click
from termcolor import colored

from .feedback import HaloFeedback
from .main import main

__all__ = ('create_instance', 'delete_instance', 'list_instances',
           'create', 'list_dbs', 'delete')


@main.group()
def db():
    pass


@db.command()
@click.option('--url')
@click.pass_context
def create_instance(ctx, url):
    from ..deploy.aws.db import create_instance as aws_create_instance
    aws_create_instance(url=url, feedback=HaloFeedback())


@db.command()
@click.pass_context
def list_instances(ctx):
    from ..deploy.aws.db import list_instances as aws_list_instances
    instances = aws_list_instances(feedback=HaloFeedback())
    if len(instances) == 0:
        print(colored('    No instances', 'grey'))
    else:
        for inst in instances:
            print(f'    {inst}')


@db.command()
@click.argument('name')
@click.pass_context
def delete_instance(ctx, name):
    from ..deploy.aws.db import delete_instance as aws_delete_instance
    aws_delete_instance(name, feedback=HaloFeedback())


@db.command()
@click.argument('deployment')
@click.option('--instance')
@click.pass_context
def create(ctx, deployment, instance):
    from ..deploy.aws.db import create_db as aws_create_db
    project = ctx.obj['project']
    aws_create_db(project, deployment, instance_name=instance, feedback=HaloFeedback())


@db.command('list')
@click.argument('deployment')
@click.pass_context
def list_dbs(ctx, deployment):
    from ..deploy.aws.db import list_dbs as aws_list_dbs
    project = ctx.obj['project']
    dbs = aws_list_dbs(project, deployment, feedback=HaloFeedback())
    if len(dbs) == 0:
        print(colored('    No databases', 'grey'))
    else:
        for db in dbs:
            print(f'    {db}')


@db.command()
@click.argument('deployment')
@click.pass_context
def delete(ctx, deployment):
    from ..deploy.aws.db import delete_db as aws_delete_db
    project = ctx.obj['project']
    aws_delete_db(project, deployment, feedback=HaloFeedback())
