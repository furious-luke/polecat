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
    # TODO: Hmm.
    try:
        from polecat.project.project import load_project
        project = load_project()
        project.prepare()
    except ModuleNotFoundError:
        # TODO: Make this nicer.
        print('Warning: unable to find Polecat project')
