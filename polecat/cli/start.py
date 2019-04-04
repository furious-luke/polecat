import click

from .main import main

__all__ = ('repo', 'project', 'app',)


@main.group()
@click.pass_context
def start(ctx):
    pass


@start.command()
@click.argument('name')
async def repo(name):
    pass


@start.command()
@click.argument('name')
async def project(name):
    pass


@start.command()
@click.argument('name')
async def app(name):
    pass
