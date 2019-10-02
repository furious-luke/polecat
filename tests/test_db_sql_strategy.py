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


def test_select_recursive(immutabledb):
    table = create_table('table', related_table='table')
    query = (
        Q(table)
        .select('col1')
        .recurse('col3')
    )
    sql = query.to_sql()
    assert sql == (
        b'WITH RECURSIVE "c0" AS (SELECT "table"."col1" AS "col1",'
        b' "table"."col3" AS "col3" FROM "table" UNION ALL SELECT'
        b' "table"."col1" AS "col1", "table"."col3" AS "col3" FROM "table"'
        b' , "c0" WHERE "table"."id" = "c0"."col3") SELECT'
        b' row_to_json(__tl) FROM (SELECT "c0"."col1" AS "col1"'
        b' FROM "c0") AS __tl'
    )


def test_filter_recursive(immutabledb):
    table = create_table('table', related_table='table')
    query = (
        Q(table)
        .filter(id=1)
        .select('col1')
        .recurse('col3')
    )
    sql = query.to_sql()
    assert sql == (
        b'WITH RECURSIVE "c0" AS (SELECT "r0"."col1" AS "col1", "r0"."col3" AS'
        b' "col3" FROM (SELECT "table"."col1" AS "col1", "table"."col3" AS'
        b' "col3" FROM "table" WHERE "table"."id" = 1) AS "r0" UNION ALL'
        b' SELECT "r1"."col1" AS "col1", "r1"."col3" AS "col3" FROM (SELECT'
        b' "table"."col1" AS "col1", "table"."col3" AS "col3" FROM "table" ,'
        b' "c0" WHERE "table"."id" = "c0"."col3") AS "r1") SELECT'
        b' row_to_json(__tl) FROM (SELECT "c0"."col1" AS "col1" FROM "c0")'
        b' AS __tl'
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


def test_insert_if_missing_strategy(immutabledb):
    table = create_table('a_table')
    query = Q(table).insert_if_missing({'col1': 1}, {'col2': 2})
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("col2", "col1") SELECT'
        b' 2, 1 WHERE NOT EXISTS (SELECT 1 FROM "a_table" WHERE'
        b' "a_table"."col1" = 1) RETURNING "id"), "c1" AS (SELECT * FROM'
        b' "c0" UNION ALL SELECT "a_table"."id" AS "id" FROM "a_table" WHERE'
        b' "a_table"."col1" = 1) SELECT row_to_json(__tl) FROM (SELECT'
        b' * FROM "c1") AS __tl'
    )


def test_insert_if_missing_strategy_with_subquery(immutabledb):
    table = create_table('a_table')
    query = Q(table).insert_if_missing({
        'col1': Q(table).select('col1')
    }, {'col2': 2})
    sql = query.to_sql()
    assert sql == (
        b'WITH "c0" AS (INSERT INTO "a_table" ("col2", "col1")'
        b' SELECT 2, (SELECT "a_table"."col1" AS "col1" FROM "a_table")'
        b' WHERE NOT EXISTS (SELECT 1 FROM "a_table" WHERE "a_table"."col1"'
        b' = (SELECT "a_table"."col1" AS "col1" FROM "a_table")) RETURNING'
        b' "id"), "c1" AS (SELECT * FROM "c0" UNION ALL SELECT'
        b' "a_table"."id" AS "id" FROM "a_table" WHERE "a_table"."col1"'
        b' = (SELECT "a_table"."col1" AS "col1" FROM "a_table"))'
        b' SELECT row_to_json(__tl) FROM (SELECT * FROM "c1") AS __tl'
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


def test_reverse_filter(immutabledb):
    b_table = create_table('b_table')
    create_table(related_table=b_table)
    query = Q(b_table).filter(a_tables__col1=1)
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM (SELECT * FROM "b_table" WHERE EXISTS'
        b' (SELECT 1 FROM "a_table" WHERE "b_table"."id" = "a_table"."col3"'
        b' AND "a_table"."col1" = 1)) AS __tl'
    )


def test_join(immutabledb):
    table = create_table()
    query = Q(table).select('col1').join()
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM (SELECT string_agg("r0"."col1", " ")'
        b' AS "col1" FROM (SELECT "a_table"."col1" AS "col1" FROM "a_table")'
        b' AS "r0") AS __tl'
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
