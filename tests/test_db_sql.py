from polecat.db.sql import Q, S

from .models import Address, Movie


def test_insert_sql(db):
    inst = Address(country='AU')
    assert getattr(inst, 'id', None) is None
    result = Q(inst).insert().execute()
    assert inst.id is not None


def test_insert_and_select(db, factory):
    actor = factory.Actor()
    movie = Movie(title='test', star=actor)
    (
        Q(movie)
        .insert()
        .select('title', star=S('first_name', 'last_name'))
        .execute()
    )
    # assert getattr(inst, 'id', None) is None
    # result = Q(inst).insert().execute()
    # assert inst.id is not None


def test_select_sql(db, factory):
    factory.Movie.create_batch(10)
    sql, args = Q(Movie).select('id', 'title', star=S('id', 'first_name', 'last_name', address=S('id', 'country'))).evaluate()
    # print(sql.as_string(db))
    # db.execute(sql)
    # for row in db.fetchall():
    #     print(row)


def test_get_sql(db, factory):
    factory.Movie.create_batch(2)
    sql, args = Q(Movie).get(star__id=1).select('id', 'title').evaluate()
    # print(sql.as_string(db))
