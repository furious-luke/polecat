from polecat.db.schema import Column, RelatedColumn, Table


def create_table(name=None, related_table=None):
    columns = [
        Column('id', 'int', primary_key=True),
        Column('col1', 'int'),
        Column('col2', 'int')
    ]
    if related_table:
        columns.append(
            RelatedColumn('col3', related_table, related_column='a_tables')
        )
    table = Table(name or 'a_table', columns)
    table.bind_all_columns()
    return table
