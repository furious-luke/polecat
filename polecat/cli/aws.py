import click

from .config import update_config
from .feedback import HaloFeedback
from .main import main

__all__ = ('initialise',)


@main.group()
@click.pass_context
def aws(ctx):
    pass


@aws.command()
@click.argument('bucket')
def initialise(bucket):
    from ..deploy.aws.initialise import initialise as aws_initialise
    from botocore.exceptions import ClientError
    try:
        aws_initialise(bucket, feedback=HaloFeedback())
    except ClientError as e:
        if e.response['Error']['Code'] == 'IllegalLocationConstraintException':
            print('\nPlease confirm you have correctly setup AWS for use on your machine.')
            print('You may need to specify your AWS credentials in your environment.\n')
        else:
            raise
    update_config({
        'bucket': bucket
    })
