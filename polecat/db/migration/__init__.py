from ...model.registry import model_registry, role_registry
from ..decorators import dbcursor
from .migration import Migration
from .operation import CreateExtension, CreateModel, CreateRole


@dbcursor
def migrate(cursor):
    migration = from_models()
    migration.forward(cursor=cursor)


def from_models():
    operations = [
        CreateExtension('chkpass')
    ]
    operations.extend(
        operation_from_role(role)
        for role in role_registry
    )
    # TODO: Chain with above?
    operations.extend(
        operation_from_model(model)
        for model in model_registry
    )
    return Migration(operations)


def operation_from_model(model):
    # TODO
    return CreateModel(
        model.__name__,
        model.Meta.fields.values(),
        model.Meta.options
    )


def operation_from_role(role):
    return CreateRole(
        role.Meta.name,
        role.parents,
        role.Meta.options
    )
