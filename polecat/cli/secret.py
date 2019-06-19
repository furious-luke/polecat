import click
from termcolor import colored

from .feedback import HaloFeedback
from .main import main

__all__ = ('create_secret', 'list_secrets')


@main.group()
@click.pass_context
def secret(ctx):
    pass


@secret.command('create')
@click.pass_context
@click.argument('deployment')
@click.argument('key')
@click.argument('value')
def create_secret(ctx, deployment, key, value):
    from ..deploy.aws.secret import create_secret as aws_create_secret
    project = ctx.obj['project']
    aws_create_secret(project, deployment, key, value, feedback=HaloFeedback())


@secret.command('list')
@click.pass_context
@click.argument('deployment')
def list_secrets(ctx, deployment):
    from ..deploy.aws.secret import list_secrets as aws_list_secrets
    project = ctx.obj['project']
    secrets = aws_list_secrets(project, deployment, feedback=HaloFeedback())
    if len(secrets) == 0:
        print(colored('    No secrets', 'grey'))
    else:
        for secret, value in secrets.items():
            print(f'    {secret} = {value}')
