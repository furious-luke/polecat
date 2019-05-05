import shutil
from pathlib import Path

import click

from ..utils import get_data_dir
from .main import main

__all__ = ('helloworld',)


@main.group()
@click.pass_context
def example(ctx):
    pass


@example.command()
def helloworld():
    src = get_data_dir() / 'examples' / 'helloworld'
    dst = Path.cwd() / 'helloworld'
    shutil.copytree(src, dst)


@example.command()
def starwars():
    src = get_data_dir() / 'examples' / 'starwars'
    dst = Path.cwd() / 'starwars'
    shutil.copytree(src, dst)
