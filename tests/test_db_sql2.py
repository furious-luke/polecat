from polecat.db.sql2.expression import Insert, Select

from .schema import create_table


def test_select_expression(testdb):
    table = create_table()
    expr = Select(
        table,
        ['col1'],
        {
            'rename': Select(table, ['id'])
        }
    )
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == b'SELECT "a_table"."col1" AS "col1", (SELECT "a_table"."id" AS "id" FROM "a_table") AS "rename" FROM "a_table"'


def test_insert_expression(testdb):
    b_table = create_table('b_table')
    a_table = create_table(related_table=b_table)
    expr = Insert(
        a_table,
        {
            'col1': 1,
            'col3': Insert(
                b_table,
                {
                    'col2': 2
                }
            )
        },
        ['col1', 'col3']
    )
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == b'INSERT INTO "a_table" ("col1", "col3") VALUES (1, (INSERT INTO "b_table" ("col2") VALUES (2) RETURNING "id")) RETURNING "col1", "col3", "id"'
