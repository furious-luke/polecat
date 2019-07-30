from polecat.db.query import Q, S
from polecat.db.session import Session

from .models import DefaultRole
from .schema import create_table


def test_select_strategy_unnested(immutabledb):
    table = create_table()
    query = Q(table).select('col1', 'col2')
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM ('
        b'SELECT "a_table"."col1" AS "col1", "a_table"."col2" AS "col2"'
        b' FROM "a_table") AS __tl'
    )


def test_select_strategy_lateral(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).select('col1', 'col2', col3=S('col1', 'col2'))
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM (SELECT "t0"."col1" AS "col1",'
        b' "t0"."col2" AS "col2", "j0" AS "col3" FROM "a_table" AS "t0"'
        b' LEFT JOIN LATERAL (SELECT "b_table"."col1" AS "col1",'
        b' "b_table"."col2" AS "col2" FROM "b_table" WHERE "b_table"."id"'
        b' = "t0"."col3") AS "j0" ON TRUE) AS __tl'
    )


def test_select_strategy_reverse_lateral(immutabledb):
    b_table = create_table('b_table')
    create_table('a_table', related_table=b_table)
    query = Q(b_table).select('col1', 'col2', a_tables=S('col1', 'col2'))
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM (SELECT "t0"."col1" AS "col1",'
        b' "t0"."col2" AS "col2", "j0"."array_agg" AS "a_tables" FROM'
        b' "b_table" AS "t0" LEFT JOIN LATERAL (SELECT array_agg("a0")'
        b' FROM (SELECT "a_table"."col1" AS "col1", "a_table"."col2" AS'
        b' "col2" FROM "a_table" WHERE "a_table"."col3" = "t0".id) AS'
        b' "a0") AS "j0" ON TRUE) AS __tl'
    )


def test_select_strategy_detached(immutabledb):
    a_table = create_table('a_table')
    b_table = create_table('b_table')
    b_query = Q(b_table).select('col1', 'col2')
    a_query = Q(a_table).select('col1', sub=b_query)
    sql = a_query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM ('
        b'SELECT "t0"."col1" AS "col1", (SELECT "b_table"."col1" AS "col1",'
        b' "b_table"."col2" AS "col2" FROM "b_table") AS "sub" FROM'
        b' "a_table" AS "t0"'
        b') AS __tl'
    )


def test_insert_strategy_unnested(immutabledb):
    table = create_table('a_table')
    query = Q(table).insert(col1=1, col2=2)
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("col1", "col2") VALUES (1, 2)'
        b' RETURNING "id") SELECT row_to_json(__tl) FROM (SELECT * FROM "c0")'
        b' AS __tl'
    )


def test_insert_strategy_with_value_subquery(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).insert(
        col1=1,
        col3=Q(b_table).select('id')
    )
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("col1", "col3") VALUES'
        b' (1, (SELECT "b_table"."id" AS "id" FROM "b_table")) RETURNING'
        b' "id") SELECT row_to_json(__tl) FROM (SELECT * FROM "c0") AS __tl'
    )


def test_insert_strategy_with_subquery(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    query = Q(a_table).insert(Q(a_table).select('id'))
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("id") (SELECT "a_table"."id"'
        b' AS "id" FROM "a_table") RETURNING "id") SELECT'
        b' row_to_json(__tl) FROM (SELECT * FROM "c0") AS __tl'
    )


def test_insert_strategy_with_nesting(immutabledb):
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
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "b_table" ("col2") VALUES (2)'
        b' RETURNING "id"), "c1" AS (INSERT INTO "a_table"'
        b' ("col1", "col3") VALUES (1, (SELECT "c0"."id" AS "id" FROM'
        b' "c0")) RETURNING "id") SELECT row_to_json(__tl) FROM (SELECT'
        b' * FROM "c1") AS __tl'
    )


def test_insert_strategy_with_explicit_reverse(immutabledb):
    b_table = create_table('b_table')
    a_table = create_table('a_table', related_table=b_table)
    b_query = Q(b_table).insert(col1=1)
    a_queries = Q.common(
        Q(a_table).insert(col1=2, col3=b_query),
        Q(a_table).insert(col2=3, col3=b_query)
    )
    sql = a_queries.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "b_table" ("col1") VALUES (1) RETURNING'
        b' "id"), "c1" AS (INSERT INTO "a_table" ("col1", "col3") VALUES (2,'
        b' (SELECT "c0"."id" AS "id" FROM "c0")) RETURNING "id"), "c2" AS'
        b' (INSERT INTO "a_table" ("col2", "col3") VALUES (3, (SELECT'
        b' "c0"."id" AS "id" FROM "c0")) RETURNING "id") SELECT'
        b' row_to_json(__tl) FROM (SELECT * FROM "c2") AS __tl'
    )


def test_insert_strategy_with_implicit_reverse(immutabledb):
    b_table = create_table('b_table')
    create_table('a_table', related_table=b_table)
    b_query = Q(b_table).insert(
        col1=1,
        a_tables=[
            {'col1': 2},
            {'col2': 3}
        ]
    )
    sql = b_query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "b_table" ("col1") VALUES (1) RETURNING'
        b' "id"), "c1" AS (INSERT INTO "a_table" ("col1", "col3") VALUES'
        b' (2, (SELECT "c0"."id" AS "id" FROM "c0")) RETURNING "id"), "c2"'
        b' AS (INSERT INTO "a_table" ("col2", "col3") VALUES (3, (SELECT'
        b' "c0"."id" AS "id" FROM "c0")) RETURNING "id") SELECT'
        b' row_to_json(__tl) FROM "c0" AS __tl'
    )


def test_update_strategy_with_nesting(immutabledb):
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
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (UPDATE "b_table" SET ("col2") = ROW (2) RETURNING "id"),'
        b' "c1" AS (UPDATE "a_table" SET ("col1", "col3") = ROW (1, (SELECT'
        b' "c0"."id" AS "id" FROM "c0")) RETURNING "id") SELECT'
        b' row_to_json(__tl) FROM (SELECT * FROM "c1") AS __tl'
    )


def test_update_strategy_with_filter(immutabledb):
    table = create_table()
    query = (
        Q(table)
        .filter(col1=1)
        .update(col2=2)
    )
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (UPDATE "a_table" SET ("col2") = ROW (2) WHERE'
        b' "a_table"."col1" = 1 RETURNING "id") SELECT row_to_json(__tl)'
        b' FROM (SELECT * FROM "c0") AS __tl'
    )


def test_multiple_inserts(immutabledb):
    table = create_table()
    query = Q(table).insert(col1=1).insert(col1=2)
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("col1") VALUES (1) RETURNING'
        b' "id"), "c1" AS (INSERT INTO "a_table" ("col1") VALUES (2)'
        b' RETURNING "id") SELECT row_to_json(__tl) FROM (SELECT'
        b' * FROM "c1") AS __tl'
    )


def test_insert_and_select_returning(immutabledb):
    table = create_table()
    query = Q(table).insert(col1=1).select('col1', 'col2')
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("col1") VALUES (1) RETURNING'
        b' "id", "col1", "col2") SELECT row_to_json(__tl) FROM (SELECT'
        b' "c0"."col1" AS "col1", "c0"."col2" AS "col2" FROM "c0") AS __tl'
    )


def test_delete_strategy_unnested(immutabledb):
    table = create_table()
    query = Q(table).delete()
    sql = query.to_sql()
    assert sql == b'DELETE FROM "a_table"'


def test_multiple_deletes(immutabledb):
    table = create_table()
    query = Q(table).delete().delete()
    sql = query.to_sql()
    assert sql == b'WITH "c0" AS (DELETE FROM "a_table") DELETE FROM "a_table"'


def test_filter_and_select(immutabledb):
    table = create_table()
    query = Q(table).filter(col2=2).select('col1')
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM (SELECT "r0"."col1" AS "col1" FROM'
        b' (SELECT "a_table"."col1" AS "col1" FROM "a_table" WHERE'
        b' "a_table"."col2" = 2) AS "r0") AS __tl'
    )


def test_filter_and_delete(immutabledb):
    table = create_table()
    query = Q(table).filter(id=1).delete()
    sql = query.to_sql()
    assert sql == (
        b'DELETE FROM "a_table" WHERE "a_table"."id" = 1'
    )


def test_filter_only(immutabledb):
    table = create_table()
    query = Q(table).filter(col2=2)
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM ('
        b'SELECT * FROM "a_table" WHERE "a_table"."col2" = 2'
        b') AS __tl'
    )


def test_session_with_role_and_variables(immutabledb):
    table = create_table()
    query = (
        Q(table, session=Session(DefaultRole.Meta.dbrole, {'a': 1}))
        .select()
    )
    sql = query.to_sql()
    assert sql == (
        b'SET LOCAL ROLE "default"; SET LOCAL "a" TO 1; SELECT'
        b' row_to_json(__tl) FROM (SELECT * FROM "a_table") AS __tl'
    )
