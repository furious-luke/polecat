import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('build',)


@main.command()
@click.option('--source')
@click.option('--local-package', '-l', multiple=True)
@click.pass_context
def build(ctx, source, local_package):
    from ..deploy.aws.build import build as aws_build
    project = ctx.obj['project']
    aws_build(project, source, local_package, feedback=HaloFeedback())
