from ...db.schema import Access as DBAccess
from ...db.schema import Role as DBRole
from ...db.schema import Schema
from ..defaults import default_blueprint
from ..field import MutableField, ReverseField
from .build import TableBuilder


def create_schema():
    table_builder = TableBuilder()
    tables = [
        table_builder.build(model)
        for model in default_blueprint.iter_models()
    ]
    roles = [
        role_to_dbrole(role)
        for role in default_blueprint.iter_roles()
    ]
    access = [
        access_to_dbaccess(access)
        for access in default_blueprint.iter_access()
    ]
    schema = Schema(tables, roles=roles, access=access)
    schema.bind()
    return schema


def role_to_dbrole(role):
    dbrole = getattr(role.Meta, 'dbrole', None)
    if not dbrole:
        dbrole = DBRole(
            role.Meta.role,
            parents=[
                role_to_dbrole(parent)
                for parent in role.parents
            ],
            app=role.Meta.app
        )
        role.Meta.dbrole = dbrole
    return dbrole


def access_to_dbaccess(access):
    dbaccess = getattr(access, 'dbaccess', None)
    if not dbaccess:
        dbaccess = DBAccess(
            access.entity.Meta.table,  # TODO: Generalise.
            all=[
                role_to_dbrole(role)
                for role in access.all
            ],
            select=[
                role_to_dbrole(role)
                for role in access.select
            ],
            insert=[
                role_to_dbrole(role)
                for role in access.insert
            ],
            update=[
                role_to_dbrole(role)
                for role in access.update
            ],
            delete=[
                role_to_dbrole(role)
                for role in access.delete
            ],
            app=access.app
        )
        access.dbaccess = dbaccess
    return dbaccess


def model_to_values(model, exclude_fields=None):
    exclude_fields = exclude_fields or ()
    values = {}
    for field_name, field in model.Meta.fields.items():
        if field_name in exclude_fields:
            continue
        if not isinstance(field, (MutableField, ReverseField)):
            continue
        if not hasattr(model, field_name):
            continue
        values[field_name] = field.to_outgoing(
            model,
            getattr(model, field_name)
        )
    return values


def set_values_on_model(values, model):
    for field_name, field in model.Meta.fields.items():
        if not isinstance(field, MutableField):
            continue
        if field_name not in values:
            continue
        setattr(model, field_name, field.from_incoming(
            model,
            values[field_name]
        ))
