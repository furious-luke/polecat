from polecat.db.schema import Column, RelatedColumn, Table


def test_create_from_migrations():
    a_table = Table(
        'a_table',
        columns=[
            Column('col1', 'int'),
            RelatedColumn('col2', 'b_table', related_column='a_tables')
        ]
    )
    b_table = Table(
        'b_table',
        columns=[
            Column('col1', 'text')
        ]
    )
    Table.bind_all_tables()
    assert isinstance(a_table.C.col2.related_table, Table)
    assert b_table.C.a_tables is not None
