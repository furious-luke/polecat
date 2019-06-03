from polecat.db.query import Q, S
from polecat.db.sql2.strategy import Strategy

from .schema import create_table


def test_select_strategy_unnested(testdb):
    table = create_table()
    query = Q(table).select('col1', 'col2')
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'SELECT "a_table"."col1" AS "col1", "a_table"."col2"'
        b' AS "col2" FROM "a_table"'
    )


def test_select_strategy_lateral(testdb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).select('col1', 'col2', col3=S('col1', 'col2'))
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'SELECT "t0"."col1" AS "col1", "t0"."col2" AS "col2", "j1" AS "col3"'
        b' FROM "a_table" AS "t0" LEFT JOIN LATERAL (SELECT "b_table"."col1"'
        b' AS "col1", "b_table"."col2" AS "col2" FROM "b_table") AS "j1" ON'
        b' "j1".id = "t0"."col3"'
    )


def test_select_strategy_detached(testdb):
    a_table = create_table('a_table')
    b_table = create_table('b_table')
    b_query = Q(b_table).select('col1', 'col2')
    a_query = Q(a_table).select('col1', sub=b_query)
    strategy = Strategy()
    expr = strategy.parse(a_query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'SELECT "t0"."col1" AS "col1", (SELECT "b_table"."col1" AS "col1",'
        b' "b_table"."col2" AS "col2" FROM "b_table") AS "sub" FROM'
        b' "a_table" AS "t0"'
    )


def test_insert_strategy_unnested(testdb):
    table = create_table('a_table')
    query = Q(table).insert(col1=1, col2=2)
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'INSERT INTO "a_table" ("col1", "col2") VALUES (1, 2)'
        b' RETURNING "id"'
    )


def test_insert_strategy_with_value_subquery(testdb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).insert(
        col1=1,
        col3=Q(b_table).select('id')
    )
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'INSERT INTO "a_table" ("col1", "col3") VALUES (1, (SELECT'
        b' "b_table"."id" AS "id" FROM "b_table")) RETURNING "id"'
    )


def test_insert_strategy_with_subquery(testdb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).insert(Q(a_table).select('id'))
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'INSERT INTO "a_table" ("id") (SELECT "a_table"."id" AS "id" FROM'
        b' "a_table") RETURNING "id"'
    )


def test_insert_strategy_with_nesting(testdb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).insert(
        col1=1,
        col3=(
            Q(b_table)
            .insert(col2=2)
            .select('id')
        )
    )
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "b_table" ("col2") VALUES (2) RETURNING'
        b' "id") INSERT INTO "a_table" ("col1", "col3") VALUES (1, (SELECT'
        b' "c0"."id" AS "id" FROM "c0")) RETURNING "id"'
    )


def test_update_strategy_with_nesting(testdb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).update(
        col1=1,
        col3=(
            Q(b_table)
            .update(col2=2)
            .select('id')
        )
    )
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'WITH "c0" AS (UPDATE "b_table" SET ("col2") = (2) RETURNING'
        b' "id") UPDATE "a_table" SET ("col1", "col3") = (1, (SELECT'
        b' "c0"."id" AS "id" FROM "c0")) RETURNING "id"'
    )


def test_multiple_inserts(testdb):
    table = create_table()
    query = Q(table).insert(col1=1).insert(col1=2)
    strategy = Strategy()
    expr = strategy.parse(query)
    sql = testdb.mogrify(*expr.to_sql())
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("col1") VALUES (1)'
        b' RETURNING "id") INSERT INTO "a_table" ("col1") VALUES (2)'
        b' RETURNING "id"'
    )
