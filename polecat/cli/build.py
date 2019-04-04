import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('build',)


@main.command()
@click.option('--source')
def build(source):
    from ..deploy.aws.build import build as aws_build
    aws_build(source, feedback=HaloFeedback())
