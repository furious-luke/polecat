import click

from .main import main

__all__ = ('show',)


@main.group()
@click.pass_context
def app(ctx):
    pass


@app.command()
def show():
    from ..project.project import load_project
    project = load_project()
    project.prepare()
    print(project.apps)
