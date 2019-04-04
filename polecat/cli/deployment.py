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
@click.argument('project')
@click.argument('deployment')
def create_deployment(project, deployment):
    from ..deploy.aws.deployment import create_deployment as aws_create_deployment
    aws_create_deployment(project, deployment, feedback=HaloFeedback())


@deployment.command('list')
@click.argument('project')
def list_deployments(project):
    from ..deploy.aws.deployment import list_deployments as aws_list_deployments
    deployments = aws_list_deployments(project, feedback=HaloFeedback())
    if len(deployments) == 0:
        print(colored('    No deployments', 'grey'))
    else:
        for dep in deployments:
            print(f'    {dep}')
