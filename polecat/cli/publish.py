import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('publish', 'unpublish')


@main.command()
@click.argument('deployment')
@click.argument('domain')
@click.option('--certificate')
@click.option('--zone')
@click.pass_context
def publish(ctx, deployment, domain, certificate, zone):
    from ..deploy.aws.publish import publish as aws_publish
    project = ctx.obj['project']
    aws_publish(project, deployment, domain, certificate, zone, feedback=HaloFeedback())


@main.command()
@click.argument('deployment')
@click.argument('domain')
@click.pass_context
def unpublish(ctx, deployment, domain):
    from ..deploy.aws.publish import unpublish as aws_unpublish
    project = ctx.obj['project']
    aws_unpublish(project, deployment, domain, feedback=HaloFeedback())
