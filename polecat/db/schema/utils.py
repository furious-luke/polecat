def table_to_identifier(table):
    if isinstance(table, str):
        ident = table
    else:
        ident = table.name
        if table.app:
            ident = f'{app}.{ident}'
    return ident


def column_to_identifier(column):
    if isinstance(column, str):
        ident = column
    else:
        ident = column.name
    return ident