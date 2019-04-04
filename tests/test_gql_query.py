from polecat.graphql import execute_query, make_graphql_schema

from .models import *  # noqa
from .queries import all_movies_query, authenticate_query

# from polecat.graphql.utils import print_schema



def test_schema():
    schema = make_graphql_schema()
    # print_schema(schema)


def test_query(db, factory):
    schema = make_graphql_schema()
    factory.Movie.create_batch(5)
    result = execute_query(schema, all_movies_query)
    assert result.errors is None
    assert len(result.data['allMovies']) == 5
    for movie in result.data['allMovies']:
        assert movie.get('star') is not None
        assert movie['star'].get('address') is not None


def test_mutation(db, factory):
    schema = make_graphql_schema()
    factory.User.create(email='test', password='test')
    result = execute_query(schema, authenticate_query, {
        'email': 'test',
        'password': 'test'
    }, reraise=True)
    assert result.errors is None
    assert len(result.data['authenticate']['token']) > 0
