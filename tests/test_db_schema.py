from polecat.db.schema import (Column, FloatColumn, IntColumn, RelatedColumn,
                               Schema, Table)


def test_create_from_migrations():
    a_table = Table(
        'a_table',
        columns=[
            IntColumn('col1'),
            RelatedColumn('col2', 'b_table', related_column='a_tables')
        ]
    )
    b_table = Table(
        'b_table',
        columns=[
            Column('col1', 'text')
        ]
    )
    schema = Schema()
    schema.add_table(a_table, b_table)
    schema.bind()
    assert isinstance(a_table.C.col2.related_table, Table)
    assert b_table.C.a_tables is not None


def test_table_equality():
    a_table = Table('a_table', columns=[IntColumn('col1')])
    b_table = Table('a_table', columns=[IntColumn('col1')])
    assert a_table.signature == b_table.signature
    assert a_table == b_table


def test_tables_differ_on_column_difference():
    a_table = Table('a_table', columns=[IntColumn('col1')])
    b_table = Table('a_table', columns=[IntColumn('col2')])
    assert a_table.signature == b_table.signature
    assert a_table != b_table


def test_column_equality():
    a_col = IntColumn('col1')
    b_col = IntColumn('col1')
    assert a_col.signature == b_col.signature
    assert a_col == b_col


def test_columns_differ_on_name_difference():
    a_col = IntColumn('col1')
    b_col = IntColumn('col2')
    assert a_col.signature != b_col.signature
    assert a_col != b_col


def test_columns_differ_on_type_difference():
    a_col = IntColumn('col1')
    b_col = FloatColumn('col1')
    assert a_col.signature == b_col.signature
    assert a_col != b_col
