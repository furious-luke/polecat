from functools import singledispatch

from ...db.schema import (BoolColumn, FloatColumn, IntColumn, JSONColumn,
                          PasswordColumn, PointColumn, RelatedColumn,
                          SerialColumn, TextColumn, TimestampColumn,
                          UUIDColumn, DateColumn)
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
def convert_field(field, builder):
    raise NotImplementedError


@convert_field.register(field.TextField)
@convert_field.register(field.EmailField)
@convert_field.register(field.PhoneField)
def convert_textfield(field, builder):
    return create_column_from_field(field, TextColumn, max_length=field.length)


@convert_field.register(field.PasswordField)
def convert_passwordfield(field, builder):
    return create_column_from_field(field, PasswordColumn)


@convert_field.register(field.BoolField)
def convert_boolfield(field, builder):
    return create_column_from_field(field, BoolColumn)


@convert_field.register(field.IntField)
def convert_intfield(field, builder):
    return create_column_from_field(field, IntColumn)


@convert_field.register(field.SerialField)
def convert_serialfield(field, builder):
    return create_column_from_field(field, SerialColumn)


@convert_field.register(field.FloatField)
def convert_floatfield(field, builder):
    return create_column_from_field(field, FloatColumn)


@convert_field.register(field.DateField)
def convert_datefield(field, builder):
    return create_column_from_field(field, DateColumn)


@convert_field.register(field.DatetimeField)
def convert_datetimefield(field, builder):
    return create_column_from_field(field, TimestampColumn)


@convert_field.register(field.UUIDField)
def convert_uuidfield(field, builder):
    return create_column_from_field(field, UUIDColumn)


@convert_field.register(field.JSONField)
def convert_jsonfield(field, builder):
    return create_column_from_field(field, JSONColumn)


@convert_field.register(field.PointField)
@convert_field.register(field.GCSPointField)
def convert_pointfield(field, builder):
    return create_column_from_field(field, PointColumn)


@convert_field.register(field.RelatedField)
def convert_relatedfield(field, builder):
    return RelatedColumn(
        field.name,
        builder.build(field.other),
        related_column=field.related_name,
        unique=field.unique,
        null=field.null,
        primary_key=field.primary_key,
        default=field.default,
        on_delete=field.on_delete
    )
