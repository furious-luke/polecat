from polecat.model.db.query import Q, S

from .models import Actor


def test_query_model(testdb):
    query = (
        Q(Actor)
        .select(
            'first_name',
            address=S('country')
        )
    )
    sql = query.to_sql()
    assert sql == (
        b'SELECT row_to_json(__tl) FROM (SELECT "t0"."first_name" AS'
        b' "first_name", "j0" AS "address" FROM "actor" AS "t0" LEFT JOIN'
        b' LATERAL (SELECT "address"."country" AS "country" FROM "address"'
        b' WHERE "address"."id" = "t0"."address") AS "j0" ON TRUE) AS __tl'
    )
