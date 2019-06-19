import click

from .config import load_config


@click.group()
@click.pass_context
@click.option('--project', '-p')
def main(ctx, project):
    ctx.obj.update(load_config())
    if project:
        ctx.obj['project'] = project
