import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('deploy', 'undeploy')


@main.command()
@click.argument('project')
@click.option('--deployment')
@click.option('--dry-run', is_flag=True)
@click.pass_context
def deploy(ctx, project, deployment, dry_run):
    from ..deploy.aws.deploy import deploy as aws_deploy
    bucket = ctx.obj['bucket']
    aws_deploy(project, bucket, deployment, dry_run, feedback=HaloFeedback())


@main.command()
@click.argument('project')
@click.argument('deployment')
@click.argument('domain')
def undeploy(project, deployment, domain):
    from ..deploy.aws.publish import unpublish as aws_unpublish
    aws_unpublish(project, deployment, domain, feedback=HaloFeedback())
