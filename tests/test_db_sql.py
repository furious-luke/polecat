import pytest
from polecat.model.db import Q, S, Session
from psycopg2 import ProgrammingError

from .models import Address, DefaultRole, Movie, Store, User, UserRole


def test_insert_sql(db):
    inst = Address(country='AU')
    assert getattr(inst, 'id', None) is None
    Q(inst).insert().into(inst)
    assert inst.id is not None


def test_insert_sql_with_app(db):
    inst = User(email='test@test.org')
    assert getattr(inst, 'id', None) is None
    Q(inst).insert().into(inst)
    assert inst.id is not None


def test_insert_reverse_sql(db):
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
        .into(movie)
    )
    assert getattr(movie, 'id', None) is None


def test_insert_subquery(db, factory):
    store = factory.Store()
    copied_store = (
        Q(Store)
        .insert(
            Q(Store)
            .filter(id=1)
            .select('name')
        )
        .select('id', 'name')
        .get()
    )
    assert store.id != copied_store['id']
    assert store.name == copied_store['name']


def test_bulk_insert(db, factory):
    query = (
        Q(Address).bulk_insert(
            ['country'],
            [('AU',), ('US',)]
        )
        .select('id', 'country')
    )
    results = list(query)
    assert len(results) == 2
    assert results[0]['id'] == 1
    assert results[0]['country'] == 'AU'
    assert results[1]['id'] == 2
    assert results[1]['country'] == 'US'


def test_update_sql(db):
    inst = Address(country='AU')
    Q(inst).insert().into(inst)
    init_id = inst.id
    (
        Q(inst)
        .update(country='NZ')
        .select('country')
        .into(inst)
    )
    assert inst.id == init_id
    assert inst.country == 'NZ'


def test_select_sql(db, factory):
    factory.Movie.create_batch(10)
    (
        Q(Movie)
        .select(
            'id',
            'title',
            star=S(
                'id',
                'first_name',
                'last_name',
                address=S('id', 'country')
            )
        )
        .execute()
    )


def test_get_sql(db, factory):
    factory.Movie.create_batch(2)
    (
        Q(Movie)
        .filter(star__id=1)
        .select('id', 'title')
        .execute()
    )


def test_get_sql_nested(db, factory):
    factory.Movie.create_batch(2)
    (
        Q(Movie)
        .filter(star__id=1)
        .select('id', star=S('id'))
        .execute()
    )


def test_delete_sql(db, factory):
    movie = factory.Movie.create()
    (
        Q(movie)
        .delete()
        .execute()
    )


def test_delete(db, factory):
    movie = factory.Movie.create()
    result = (
        Q(movie)
        .filter(id=movie.id)
    )
    result = [r for r in result]
    assert len(result) == 1
    (
        Q(movie)
        .delete()
        .execute()
    )
    result = (
        Q(movie)
        .filter(id=movie.id)
    )
    result = [r for r in result]
    assert len(result) == 0


def test_set_role(db):
    with pytest.raises(ProgrammingError):
        (
            Q(Address, session=Session(DefaultRole.Meta.dbrole))
            .select('id')
            .execute()
        )
    (
        Q(Address)
        .select('id')
        .execute()
    )
    (
        Q(Address, session=Session(UserRole.Meta.dbrole))
        .select('id')
        .execute()
    )
