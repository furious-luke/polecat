import click

from .feedback import HaloFeedback, cli_feedback
from .main import main

__all__ = ('build',)


@main.command()
@click.option('--source')
@click.option('--local-package', '-l', multiple=True)
@click.pass_context
@cli_feedback('Build server code')
def build(ctx, source, local_package, feedback=None):
    from ..deploy.aws.build import build as aws_build
    project = ctx.obj['project']
    aws_build(project, source, local_package, feedback=feedback)
