import click
from termcolor import colored

from .feedback import HaloFeedback
from .main import main

__all__ = ('deploy', 'undeploy')


@main.command()
@click.option('--deployment')
@click.option('--dry-run', is_flag=True)
@click.pass_context
def deploy(ctx, deployment, dry_run):
    from ..deploy.aws.deploy import deploy as aws_deploy
    project = ctx.obj['project']
    bucket = ctx.obj['bucket']
    urls = aws_deploy(project, bucket, deployment, dry_run, feedback=HaloFeedback())
    for deployment, url in urls.items():
        print(f'  {deployment}: {colored(url, "green")}')


@main.command()
@click.option('--deployment')
@click.pass_context
def undeploy(ctx, deployment):
    from ..deploy.aws.deploy import undeploy as aws_undeploy
    project = ctx.obj['project']
    aws_undeploy(project, deployment, feedback=HaloFeedback())
