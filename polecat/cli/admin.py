import click

from .main import main

__all__ = ('admin',)


@main.group()
@click.option('--project', '-p')
@click.option('--deployment', '-d')
@click.pass_context
def admin(ctx, project, deployment):
    ctx.obj['project'] = project
    ctx.obj['deployment'] = deployment
