import pytest
from polecat.db.sql import Q
from polecat.graphql import build_graphql_schema, execute_query
from polecat.graphql.utils import print_schema

from .models import *  # noqa
from .queries import (all_actors_query, all_addresses_query, all_movies_query,
                      authenticate_query, create_actor_and_movies_query,
                      create_actors_query, delete_movie_query,
                      get_address_query)


def test_schema():
    schema = build_graphql_schema()
    # print_schema(schema)


def test_query(db, factory):
    schema = build_graphql_schema()
    factory.Movie.create_batch(5)
    result = execute_query(schema, all_movies_query)
    assert result.errors is None
    assert len(result.data['allMovies']) == 5
    for movie in result.data['allMovies']:
        assert movie.get('star') is not None
        assert movie['star'].get('address') is not None


def test_reverse_query(db, factory):
    schema = build_graphql_schema()
    movies = factory.Movie.create_batch(5)
    factory.Movie.create(star=movies[0].star)
    result = execute_query(schema, all_actors_query)
    assert result.errors is None
    assert len(result.data['allActors']) == 5
    for actor in result.data['allActors']:
        assert actor.get('moviesByStar') is not None


def test_create(db):
    schema = build_graphql_schema()
    result = execute_query(schema, create_actors_query)
    assert result.errors is None
    assert result.data['firstActor'] is not None
    assert result.data['secondActor'] is not None


def test_create_reverse(db):
    schema = build_graphql_schema()
    result = execute_query(schema, create_actor_and_movies_query)
    assert result.errors is None
    data = result.data['createActor']
    assert data['id'] is not None
    assert data['moviesByStar'] is not None
    assert len(data['moviesByStar']) == 2
    for movie in data['moviesByStar']:
        assert movie['id'] is not None


def test_delete(db, factory):
    schema = build_graphql_schema()
    movie = factory.Movie.create()
    result = execute_query(schema, delete_movie_query, {'id': movie.id})
    assert result.errors is None
    data = result.data['deleteMovie']
    assert data['id'] == movie.id
    result = Q(movie).get(id=movie.id).execute()
    assert result is None


def test_mutation(db, factory):
    schema = build_graphql_schema()
    factory.User.create(email='test', password='test')
    result = execute_query(schema, authenticate_query, {
        'email': 'test',
        'password': 'test'
    }, reraise=True)
    assert result.errors is None
    assert len(result.data['authenticate']['token']) > 0


def test_set_role(db):
    schema = build_graphql_schema()
    result = execute_query(schema, all_addresses_query, context={'role': DefaultRole})
    assert len(result.errors) > 0
    result = execute_query(schema, all_addresses_query, context={'role': UserRole})
    assert result.errors is None
    result = execute_query(schema, get_address_query, context={'role': DefaultRole})
    assert len(result.errors) > 0
    result = execute_query(schema, get_address_query, context={'role': UserRole})
    assert result.errors is None
    # TODO: Create, delete, update.
