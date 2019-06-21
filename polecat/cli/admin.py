import click

from .main import main

__all__ = ('admin',)


@main.group()
@click.option('--deployment', '-d')
@click.pass_context
def admin(ctx, deployment):
    if deployment:
        ctx.obj['deployment'] = deployment
