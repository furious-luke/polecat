import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('create', 'delete')


@main.group()
def db():
    pass


@db.command()
@click.argument('project')
@click.argument('deployment')
@click.pass_context
def create(ctx, project, deployment):
    from ..deploy.aws.db import create_db as aws_create_db
    aws_create_db(project, deployment, feedback=HaloFeedback())


@db.command()
@click.argument('project')
@click.argument('deployment')
@click.pass_context
def delete(ctx, project, deployment):
    from ..deploy.aws.db import delete_db as aws_delete_db
    aws_delete_db(project, deployment, feedback=HaloFeedback())
