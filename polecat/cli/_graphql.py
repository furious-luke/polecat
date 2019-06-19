import click

from ..deploy.server.server import Server
from ..graphql import build_graphql_schema
from ..graphql.utils import print_schema
from .main import main

__all__ = ('schema',)


@main.group()
@click.pass_context
def graphql(ctx):
    pass


@graphql.command()
def schema():
    Server()
    schema = build_graphql_schema()
    print_schema(schema)
