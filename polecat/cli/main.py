import click
from termcolor import colored

from .config import load_config


@click.group()
@click.option('--project', '-p')
@click.pass_context
def main(ctx, project):
    config, config_path = load_config()
    if config_path:
        print(f'Loaded config from {colored(config_path, "blue")}')
    ctx.obj.update(config)
    if project:
        ctx.obj['project'] = project
