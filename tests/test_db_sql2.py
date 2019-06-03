from polecat.db.sql2.expression import Insert, Select, Subquery, Update

from .schema import create_table


def test_select_expression(testdb):
    table = create_table()
    expr = Select(
        table,
        ['col1'],
        {
            'rename': Subquery(Select(table, ['id']))
        }
    )
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'SELECT "a_table"."col1" AS "col1", (SELECT "a_table"."id" AS "id"'
        b' FROM "a_table") AS "rename" FROM "a_table"'
    )


def test_insert_expression(testdb):
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
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'INSERT INTO "a_table" ("col1", "col3") VALUES (1, (INSERT INTO'
        b' "b_table" ("col2") VALUES (2) RETURNING "id")) RETURNING'
        b' "col1", "col3", "id"'
    )


def test_update_expression(testdb):
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
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'UPDATE "a_table" SET ("col1", "col3") = (1, (UPDATE "b_table" SET'
        b' ("col2") = (2) RETURNING "id")) RETURNING "col1", "col3", "id"'
    )


def test_cte_expression(testdb):
    pass
