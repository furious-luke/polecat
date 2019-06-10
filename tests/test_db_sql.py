import pytest
from polecat.db.schema import Table
from polecat.model.db import Q, S
from polecat.model.db.helpers import model_to_table
from psycopg2 import ProgrammingError

from .models import Actor, Address, DefaultRole, Movie, UserRole


def test_insert_sql(db):
    inst = Address(country='AU')
    assert getattr(inst, 'id', None) is None
    Q(inst).insert().into(inst)
    assert inst.id is not None


def test_insert_reverse_sql(db):
    model_to_table(Address)
    model_to_table(Actor)
    Table.bind_all_tables()
    inst = Address(
        country='AU',
        actors_by_address=[
            {'first_name': 'a'},
            {'first_name': 'b'}
        ]
    )
    assert getattr(inst, 'id', None) is None
    (
        Q(inst)
        .insert()
        .select(
            'id',
            'country',
            actors_by_address=S('first_name')
        )
        .into(inst)
    )
    assert inst.id is not None
    assert len(inst.actors_by_address) == 2
    for actor in inst.actors_by_address:
        assert actor.first_name is not None


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


def test_update_sql(db):
    inst = Address(country='AU')
    Q(inst).insert().execute()
    init_id = inst.id
    inst.country = 'NZ'
    Q(inst).update().execute()
    assert inst.id == init_id
    assert inst.country == 'NZ'


def test_select_sql(db, factory):
    factory.Movie.create_batch(10)
    sql, args = Q(Movie).select('id', 'title', star=S('id', 'first_name', 'last_name', address=S('id', 'country'))).evaluate()
    print(sql.as_string(db))
    # db.execute(sql)
    # for row in db.fetchall():
    #     print(row)


def test_get_sql(db, factory):
    factory.Movie.create_batch(2)
    sql, args = Q(Movie).get(star__id=1).select('id', 'title').evaluate()
    # print(sql.as_string(db))


def test_delete_sql(db, factory):
    movie = factory.Movie.create()
    sql, args = Q(movie).delete().evaluate()
    # print(sql.as_string(db))


def test_delete(db, factory):
    movie = factory.Movie.create()
    result = Q(movie).get(id=movie.id).execute()
    assert result is not None
    Q(movie).delete().execute()
    result = Q(movie).get(id=movie.id).execute()
    assert result is None


def test_set_role(db):
    with pytest.raises(ProgrammingError):
        Q(Address).select('id').execute(role=DefaultRole)
    Q(Address).select('id').execute()
    Q(Address).select('id').execute(role=UserRole)
