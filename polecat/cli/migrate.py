import click

from ..db.migration import make_migrations as db_make_migrations, migrate as db_migrate
from ..project.project import load_project
from .main import main

__all__ = ('migrate', 'empty_migration', 'make_migrations')


@main.command()
def migrate():
    project = load_project()
    project.prepare()
    db_migrate()


@main.command()
def empty_migration():
    pass


@main.command()
def make_migrations():
    project = load_project()
    project.prepare()
    db_make_migrations()
