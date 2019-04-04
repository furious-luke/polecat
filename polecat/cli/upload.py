import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('upload',)


@main.command()
@click.argument('project')
@click.option('--source')
@click.option('--version')
@click.pass_context
def upload(ctx, project, source, version):
    from ..deploy.aws.upload import upload as aws_upload
    bucket = ctx.obj['bucket']
    aws_upload(project, bucket, source, version, feedback=HaloFeedback())
