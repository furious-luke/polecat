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
    migrations = {}
    for app in app_registry:
        migrations.update(load_app_migrations(app))
    for path in migration_paths or ():
        migrations.update(load_path_migrations(path))
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
    for path in (app.path / 'migrations').iterdir():
        match = Migration.filename_prog.match(path.filename)
        if match:
            migration_class = Migration.load_migration_class(path)
            migration = migration_class(app=app.name, name=path.filename)
            migrations[f'{app.name}.{path.filename}'] = migration
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
    for app in app_registry:
        make_migrations_for_app(app)


def make_migrations_for_app(app):
    for role in app.roles:
        make_migrations_for_role(role)
    for model in app.models:
        make_migrations_for_model(model)


def make_migrations_for_role(role):
    pass


def make_migrations_for_model(model):
    pass


# def from_models():
#     operations = [
#         CreateExtension('chkpass')
#     ]
#     operations.extend(
#         operation_from_role(role)
#         for role in role_registry
#     )
#     # TODO: Chain with above?
#     operations.extend(
#         operation_from_model(model)
#         for model in model_registry
#     )
#     return Migration(operations)


# def operation_from_model(model):
#     # TODO
#     return CreateModel(
#         model.__name__,
#         model.Meta.fields.values(),
#         model.Meta.options
#     )


# def operation_from_role(role):
#     return CreateRole(
#         role.Meta.name,
#         role.parents,
#         role.Meta.options
#     )
