import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('upload', 'upload_bundle')


@main.command()
@click.option('--source')
@click.option('--version')
@click.pass_context
def upload(ctx, source, version):
    from ..deploy.aws.upload import upload as aws_upload
    project = ctx.obj['project']
    bucket = ctx.obj['bucket']
    aws_upload(project, bucket, source, version, feedback=HaloFeedback())


@main.command()
@click.option('--source')
@click.option('--version')
@click.pass_context
def upload_bundle(ctx, source, version):
    from ..deploy.aws.upload import upload_bundle as aws_upload_bundle
    project = ctx.obj['project']
    bucket = ctx.obj['bucket']
    aws_upload_bundle(project, bucket, source, version, feedback=HaloFeedback())
