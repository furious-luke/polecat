import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('publish', 'unpublish')


@main.command()
@click.argument('project')
@click.argument('deployment')
@click.argument('domain')
@click.option('--certificate')
@click.option('--zone')
def publish(project, deployment, domain, certificate, zone):
    from ..deploy.aws.publish import publish as aws_publish
    aws_publish(project, deployment, domain, certificate, zone, feedback=HaloFeedback())


@main.command()
@click.argument('project')
@click.argument('deployment')
@click.argument('domain')
def unpublish(project, deployment, domain):
    from ..deploy.aws.publish import unpublish as aws_unpublish
    aws_unpublish(project, deployment, domain, feedback=HaloFeedback())
