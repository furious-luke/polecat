import click

from .config import load_config


@click.group()
@click.pass_context
def main(ctx):
    ctx.obj.update(load_config())
