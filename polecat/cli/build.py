import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('build',)


@main.command()
@click.argument('project')
@click.option('--source')
@click.option('--local-package', '-l', multiple=True)
def build(project, source, local_package):
    from ..deploy.aws.build import build as aws_build
    aws_build(project, source, local_package, feedback=HaloFeedback())
