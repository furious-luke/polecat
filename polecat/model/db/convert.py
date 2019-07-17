from functools import singledispatch

from ...db.schema import (BoolColumn, FloatColumn, IntColumn, PasswordColumn,
                          RelatedColumn, SerialColumn, TextColumn,
                          TimestampColumn, UUIDColumn)
from .. import field


def create_column_from_field(field, type, **kwargs):
    return type(
        field.name,
        unique=field.unique,
        null=field.null,
        primary_key=field.primary_key,
        default=field.default,
        **kwargs
    )


@singledispatch
def convert_field(field):
    raise NotImplementedError


@convert_field.register(field.TextField)
@convert_field.register(field.EmailField)
@convert_field.register(field.PhoneField)
def convert_textfield(field):
    return create_column_from_field(field, TextColumn, max_length=field.length)


@convert_field.register(field.PasswordField)
def convert_passwordfield(field):
    return create_column_from_field(field, PasswordColumn)


@convert_field.register(field.BoolField)
def convert_boolfield(field):
    return create_column_from_field(field, BoolColumn)


@convert_field.register(field.IntField)
def convert_intfield(field):
    return create_column_from_field(field, IntColumn)


@convert_field.register(field.SerialField)
def convert_serialfield(field):
    return create_column_from_field(field, SerialColumn)


@convert_field.register(field.FloatField)
def convert_floatfield(field):
    return create_column_from_field(field, FloatColumn)


@convert_field.register(field.DatetimeField)
def convert_datetimefield(field):
    return create_column_from_field(field, TimestampColumn)


@convert_field.register(field.UUIDField)
def convert_uuidfield(field):
    return create_column_from_field(field, UUIDColumn)


@convert_field.register(field.PointField)
@convert_field.register(field.GCSPointField)
def convert_pointfield(field):
    return create_column_from_field(field, FloatColumn, ranks=(2,))


@convert_field.register(field.RelatedField)
def convert_relatedfield(field):
    # TODO: Dang it.
    from .helpers import model_to_table
    return RelatedColumn(
        field.name,
        model_to_table(field.other),
        related_column=field.related_name,
        unique=field.unique,
        null=field.null,
        primary_key=field.primary_key,
        default=field.default
    )
