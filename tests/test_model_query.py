from polecat.model.db.query import Q, S

from .models import Actor


def test_query_model(testdb):
    query = Q(Actor).select(
        'first_name',
        address=S('country')
    )
    sql = query.to_sql()
    assert sql == (
        b'SELECT "t0"."first_name" AS "first_name", "j0" AS "address" FROM'
        b' "actor" AS "t0" LEFT JOIN LATERAL (SELECT "address"."country" AS'
        b' "country" FROM "address") AS "j0" ON "j0".id = "t0"."address"'
    )
