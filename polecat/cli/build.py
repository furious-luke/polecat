import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('build',)


@main.command()
@click.argument('project')
@click.option('--source')
def build(project, source):
    from ..deploy.aws.build import build as aws_build
    aws_build(project, source, feedback=HaloFeedback())
