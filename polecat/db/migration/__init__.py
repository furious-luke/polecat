from pathlib import Path

from ...model.registry import model_registry, role_registry
from ...project.app import app_registry
from ..decorators import dbcursor
from .migration import Migration
from .operation import CreateExtension
from .schema import Schema


@dbcursor
def migrate(migration_paths=None, cursor=None):
    bootstrap_migrations()
    migrations = load_migrations(migration_paths)
    for migration in migrations.values():
        migration.forward(migrations, cursor=cursor)
    # # TODO: Need to execute all migrations instead of this.
    # schema = Schema.from_models()
    # migrations = schema.diff()
    # # TODO: Where the hell to put these...
    # migrations = [
    #     CreateExtension('chkpass'),
    #     *migrations
    # ]
    # for mgr in migrations:
    #     mgr.forward()


def load_migrations(migration_paths=None):
    migrations = {}
    for app in app_registry:
        migrations.update(load_app_migrations(app))
    for path in migration_paths or ():
        migrations.update(load_path_migrations(path))
    return migrations


@dbcursor
def sync(migration_paths=None, cursor=None):
    migrate(migration_paths, cursor=cursor)
    # TODO: Build schema from migrations.
    to_schema = Schema.from_models()
    migrations = to_schema.diff()  # TODO: Add in "from_schema"
    # # TODO: Where the hell to put these...
    migrations = [
        CreateExtension('chkpass'),
        *migrations
    ]
    for mgr in migrations:
        mgr.forward()


@dbcursor
def bootstrap_migrations(cursor):
    sql = (
        'CREATE TABLE IF NOT EXISTS polecat_migrations ('
        '  id serial primary key,'
        '  app varchar(256),'
        '  name text,'
        '  applied timestamptz'
        ');'
    )
    cursor.execute(sql)


def load_app_migrations(app):
    migrations = {}
    try:
        for path in (app.path / 'migrations').iterdir():
            match = Migration.filename_prog.match(path.name)
            if match:
                migration_class = Migration.load_migration_class(path)
                migration = migration_class(app=app.name, name=path.name)
                migrations[f'{app.name}.{path.name}'] = migration
                migration.set_app(app)
    except FileNotFoundError:
        pass
    return migrations


def load_path_migrations(path):
    migrations = {}
    for file_path in Path(path).iterdir():
        match = Migration.filename_prog.match(file_path.name)
        if match:
            migration_class = Migration.load_migration_class(file_path)
            migration = migration_class(name=file_path.name)
            migrations[f'{file_path.name}'] = migration
    return migrations


def make_migrations():
    migrations = load_migrations()
    # TODO: Make schema from migrations.
    to_schema = Schema.from_models()
    new_migrations = to_schema.diff()  # TODO: Add in "from_schema"
    for mgr in new_migrations:
        # TODO: Feedback?
        mgr.save()


def make_migrations_for_app(app):
    for role in app.roles:
        make_migrations_for_role(role)
    for model in app.models:
        make_migrations_for_model(model)


def make_migrations_for_role(role):
    pass


def make_migrations_for_model(model):
    pass
