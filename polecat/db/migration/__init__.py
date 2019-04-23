from ...model.registry import model_registry, role_registry
from ...project.app import app_registry
from ..decorators import dbcursor
from .migration import Migration
from .operation import CreateExtension
from .schema import Schema


@dbcursor
def migrate(cursor):
    # TODO: Need to execute all migrations instead of this.
    schema = Schema.from_models()
    migrations = schema.diff()
    # TODO: Where the hell to put these...
    migrations = [
        CreateExtension('chkpass'),
        *migrations
    ]
    for mgr in migrations:
        mgr.forward()


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
