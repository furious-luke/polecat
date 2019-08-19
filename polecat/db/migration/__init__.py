from pathlib import Path

from polecat.core.context import active_context

from ..decorators import dbcursor
from ..schema import Schema
from .differ import Differ
from .migration import Migration
from .utils import project_migrations_path


def diff_schemas(to_schema, from_schema=None):
    if from_schema is None:
        from_schema = Schema()
    return Differ().diff(from_schema, to_schema)


@dbcursor
def migrate(migration_paths=None, apps=None, cursor=None):
    bootstrap_migrations()
    migrations = load_migrations(migration_paths, apps=apps)
    schema = Schema()
    for migration in migrations.values():
        migration.forward(schema, migrations, cursor=cursor)


def load_migrations(migration_paths=None, apps=None):
    migrations = {}
    for app in apps or ():
        migrations.update(load_app_migrations(app))
    for path in migration_paths or ():
        migrations.update(load_path_migrations(path))
    migrations.update(load_path_migrations(project_migrations_path()))
    return migrations


@dbcursor
def bootstrap_migrations(cursor):
    # TODO: This is only for development purposes, and *should* fail
    # in production as production users shouldn't have superuser
    # access.
    try:
        sql = (
            'CREATE EXTENSION IF NOT EXISTS chkpass;'
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
            'CREATE EXTENSION IF NOT EXISTS pg_trgm;'
        )
        cursor.execute(sql)
    except Exception:
        # TODO: Reduce this to programming error.
        pass
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
                migration = migration_class(app=app.name, name=path.name[:-3], filename=path.name)
                migrations[f'{app.name}.{path.name[:-3]}'] = migration
                migration.set_app(app)
    except FileNotFoundError:
        pass
    return migrations


def load_path_migrations(path):
    migrations = {}
    try:
        for file_path in (Path(path) / 'migrations').iterdir():
            match = Migration.filename_prog.match(file_path.name)
            if match:
                migration_class = Migration.load_migration_class(file_path)
                migration = migration_class(name=file_path.name[:-3])
                migrations[f'{file_path.name[:-3]}'] = migration
    except FileNotFoundError:
        pass
    return migrations


def make_migrations(to_schema=None, output_path=None, apps=None, migration_paths=None):
    from_schema = Schema()
    migrations = load_migrations(apps=apps, migration_paths=migration_paths)
    for mgr in migrations.values():
        mgr.forward(schema=from_schema, migrations=migrations, schema_only=True)
    if to_schema is None:
        to_schema = active_context().db.schema
    new_migrations = diff_schemas(to_schema, from_schema)
    for mgr in new_migrations:
        # TODO: Feedback?
        mgr.save(output_path=output_path)
    return new_migrations


def make_migrations_for_app(app):
    for role in app.roles:
        make_migrations_for_role(role)
    for model in app.models:
        make_migrations_for_model(model)


def make_migrations_for_role(role):
    pass


def make_migrations_for_model(model):
    pass
