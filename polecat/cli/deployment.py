import click
from termcolor import colored

from .feedback import HaloFeedback
from .main import main

__all__ = ('create_deployment', 'list_deployments')


@main.group()
@click.pass_context
def deployment(ctx):
    pass


@deployment.command('create')
@click.argument('deployment')
@click.pass_context
def create_deployment(ctx, deployment):
    from ..deploy.aws.deployment import create_deployment as aws_create_deployment
    project = ctx.obj['project']
    aws_create_deployment(project, deployment, feedback=HaloFeedback())


@deployment.command('list')
@click.pass_context
def list_deployments(ctx):
    from ..deploy.aws.deployment import list_deployments as aws_list_deployments
    project = ctx.obj['project']
    deployments = aws_list_deployments(project, feedback=HaloFeedback())
    if len(deployments) == 0:
        print(colored('    No deployments', 'grey'))
    else:
        for dep in deployments:
            print(f'    {dep}')


@deployment.command('delete')
@click.argument('deployment')
@click.pass_context
def delete_deployment(ctx, deployment):
    from ..deploy.aws.deployment import delete_deployment as aws_delete_deployment
    project = ctx.obj['project']
    aws_delete_deployment(project, deployment, feedback=HaloFeedback())
