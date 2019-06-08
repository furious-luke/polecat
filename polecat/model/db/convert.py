from functools import singledispatch

from .. import field
from ...db.schema import Column, RelatedColumn


def create_column_from_field(field, type):
    return Column(
        field.name,
        type,
        unique=field.unique,
        null=field.null,
        primary_key=field.primary_key
    )


@singledispatch
def convert_field(field):
    raise NotImplementedError


@convert_field.register(field.TextField)
@convert_field.register(field.EmailField)
@convert_field.register(field.PhoneField)
def convert_textfield(field):
    if field.length:
        type = f'varchar({field.length})'
    else:
        type = 'text'
    return create_column_from_field(field, type)


@convert_field.register(field.PasswordField)
def convert_passwordfield(field):
    return create_column_from_field(field, 'chkpass')


@convert_field.register(field.BoolField)
def convert_boolfield(field):
    return create_column_from_field(field, 'boolean')


@convert_field.register(field.IntField)
def convert_intfield(field):
    return create_column_from_field(field, 'int')


@convert_field.register(field.FloatField)
def convert_floatfield(field):
    return create_column_from_field(field, 'float')


@convert_field.register(field.DatetimeField)
def convert_datetimefield(field):
    return create_column_from_field(field, 'timestamptz')


@convert_field.register(field.UUIDField)
def convert_uuidfield(field):
    return create_column_from_field(field, 'uuid')


@convert_field.register(field.PointField)
@convert_field.register(field.GCSPointField)
def convert_pointfield(field):
    return create_column_from_field(field, 'point')


@convert_field.register(field.RelatedField)
def convert_relatedfield(field):
    # TODO: Dang it.
    from .helpers import model_to_table
    return RelatedColumn(
        field.name,
        model_to_table(field.other),
        unique=field.unique,
        null=field.null,
        primary_key=field.primary_key
    )
