import pytest
from polecat.db.sql.expression import Insert, Select, Subquery, Update, Where

from .schema import create_table


def test_select_expression(immutabledb):
    table = create_table()
    expr = Select(
        table,
        ['col1'],
        {
            'rename': Subquery(Select(table, ['id']))
        }
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'SELECT "a_table"."col1" AS "col1", (SELECT "a_table"."id" AS "id"'
        b' FROM "a_table") AS "rename" FROM "a_table"'
    )


def test_select_expression_with_app(immutabledb):
    table = create_table()
    table.app = type('App', (), {'name': 'test'})
    expr = Select(table, ['col1'])
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == b'SELECT "test_a_table"."col1" AS "col1" FROM "test_a_table"'


def test_select_expression_with_where(immutabledb):
    table = create_table()
    expr = Select(
        table,
        ['col1'],
        where=Where(col1=1, col2=2)
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'SELECT "a_table"."col1" AS "col1" FROM "a_table" WHERE'
        b' "a_table"."col1" = 1 AND "a_table"."col2" = 2'
    )


def test_insert_expression(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table(related_table=b_table)
    expr = Insert(
        a_table,
        {
            'col1': 1,
            'col3': Subquery(
                Insert(
                    b_table,
                    {
                        'col2': 2
                    }
                )
            )
        },
        ['col1', 'col3']
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'INSERT INTO "a_table" ("col1", "col3") VALUES (1, (INSERT INTO'
        b' "b_table" ("col2") VALUES (2) RETURNING "id")) RETURNING'
        b' "col1", "col3", "id"'
    )


@pytest.mark.skip(reason='This is probably an antipattern')
def test_insert_subquery_with_all_columns(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table(related_table=b_table)
    expr = Insert(
        a_table,
        Select(
            a_table,
            where=Where(id=1)
        ),
        ['col1', 'col3']
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'INSERT INTO "a_table" SELECT * FROM "a_table" WHERE'
        b' "a_table"."id" = 1 RETURNING "col1", "col3", "id"'
    )


def test_insert_subquery_with_selected_columns(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table(related_table=b_table)
    expr = Insert(
        a_table,
        Select(
            a_table,
            ['col1', 'col3'],
            where=Where(id=1)
        ),
        ['col1', 'col3']
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'INSERT INTO "a_table" ("col1", "col3") SELECT "a_table"."col1" AS'
        b' "col1", "a_table"."col3" AS "col3" FROM "a_table" WHERE'
        b' "a_table"."id" = 1 RETURNING "col1", "col3", "id"'
    )


def test_insert_all_defaults(immutabledb):
    a_table = create_table('a_table')
    expr = Insert(a_table)
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == b'INSERT INTO "a_table" DEFAULT VALUES RETURNING "id"'


def test_update_expression(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table(related_table=b_table)
    expr = Update(
        a_table,
        {
            'col1': 1,
            'col3': Subquery(
                Update(
                    b_table,
                    {
                        'col2': 2
                    }
                )
            )
        },
        ['col1', 'col3']
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'UPDATE "a_table" SET ("col1", "col3") = ROW (1, (UPDATE "b_table" SET'
        b' ("col2") = ROW (2) RETURNING "id")) RETURNING "col1", "col3", "id"'
    )


def test_cte_expression(immutabledb):
    # TODO
    pass


def test_where_expression(immutabledb):
    table = create_table()
    where = Where(col1=1)
    sql = immutabledb.mogrify(*where.get_sql(table))
    assert sql == b'"a_table"."col1" = 1'


def test_where_expression_with_lookups(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    where = Where(col1=1, col3__col2=2)
    sql = immutabledb.mogrify(*where.get_sql(a_table))
    assert sql == (
        b'"a_table"."col1" = 1 AND EXISTS (SELECT 1 FROM "b_table" WHERE'
        b' "a_table"."col3" = "b_table"."id" AND "b_table"."col2" = 2)'
    )


def test_insert_and_select_with_where(immutabledb):
    table = create_table()
    expr = Select(
        Subquery(
            Insert(
                table,
                {
                    'col1': 1,
                },
                ['col1', 'col2']
            )
        ),
        ['col1', 'col2'],
        where=Where(col1=1)
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'SELECT "a_table"."col1" AS "col1", "a_table"."col2" AS "col2" FROM'
        b' (INSERT INTO "a_table" ("col1") VALUES (1) RETURNING "col1",'
        b' "col2", "id") WHERE "a_table"."col1" = 1'
    )
