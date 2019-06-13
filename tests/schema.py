from polecat.db.schema import IntColumn, RelatedColumn, Schema, Table


def create_table(name=None, related_table=None, schema=None):
    columns = [
        IntColumn('id', primary_key=True),
        IntColumn('col1'),
        IntColumn('col2')
    ]
    if related_table:
        columns.append(
            RelatedColumn('col3', related_table, related_column='a_tables')
        )
    table = Table(name or 'a_table', columns)
    if schema is None:
        schema = Schema()
    schema.add_table(table)
    schema.bind()
    return table
