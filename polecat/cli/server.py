import click

from .main import main

__all__ = ('server',)


@main.command()
@click.option('--production', is_flag=True, default=False,
              help='Launch in production mode.')
def server(production):
    from ..deploy.server.server import Server
    server = Server(production=production)
    server.run()
