from ..field import MutableField, ReverseField
from .build import TableBuilder


def model_to_table(model):
    table = getattr(model.Meta, 'table', None)
    if not table:
        # TODO: Should keep one around?
        builder = TableBuilder()
        table = builder.build(model)
        model.Meta.table = table
        table.bind_all_columns()
    return table


def model_to_values(model):
    values = {}
    for field_name, field in model.Meta.fields.items():
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
