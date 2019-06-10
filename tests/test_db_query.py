import pytest
from polecat.db.query import Q

from .schema import create_table


def test_select():
    table = create_table()
    Q(table).select('col1', 'col2')


def test_insert():
    table = create_table()
    Q(table).insert(col1=1, col2=2)


def test_insert_into():
    a_table = create_table()
    b_table = create_table('b_table')
    (
        Q(a_table)
        .insert(col1=1, col2=2)
        .insert_into(b_table, col1=1, col2=2)
    )


def test_nested_query_insert():
    b_table = create_table('b_table')
    a_table = create_table(b_table)
    Q(a_table).insert(
        Q(b_table)
        .insert(col1=1)
        .select('col1', 'col2')
    )


def test_nested_value_insert():
    b_table = create_table('b_table')
    a_table = create_table(related_table=b_table)
    Q(a_table).insert(
        col3={
            'col1': 1
        }
    )


def test_insert_invalid_column():
    table = create_table()
    with pytest.raises(KeyError):
        Q(table).insert(missing=1)


def test_update():
    table = create_table()
    Q(table).update(col1=1, col2=2)


def test_update_into():
    a_table = create_table()
    b_table = create_table('b_table')
    (
        Q(a_table)
        .update(col1=1, col2=2)
        .update_into(b_table, col1=1, col2=2)
    )


def test_delete():
    table = create_table()
    Q(table).delete()


def test_filter():
    table = create_table()
    Q(table).filter(col1=1, col2=2)


def test_chained_insert():
    a_table = create_table()
    (
        Q(a_table)
        .insert(col1=1, col2=2)
        .insert(col1=3, col2=4)
        .select('col2')
    )


def test_combined_queries():
    a_table = create_table()
    (
        Q.common(
            (
                Q(a_table)
                .select('col1')
            ),
            (
                Q(a_table)
                .insert(col1=1, col2=2)
                .select('col2')
            )
        )
    )
