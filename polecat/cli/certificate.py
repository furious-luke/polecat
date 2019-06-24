import click

from .feedback import HaloFeedback
from .main import main

__all__ = ('create',)


@main.group()
def certificate():
    pass


@certificate.command()
@click.argument('domain', nargs=-1)
@click.option('--name', '-n')
@click.pass_context
def create(ctx, domain, name):
    from polecat.deploy.aws.certificate import create_certificate
    create_certificate(domain, name, feedback=HaloFeedback())


@certificate.command()
@click.argument('domain')
@click.pass_context
def wait(ctx, domain):
    from polecat.deploy.aws.certificate import wait_certificate
    wait_certificate(domain, feedback=HaloFeedback())
