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
