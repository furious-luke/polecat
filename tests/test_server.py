import pytest
import ujson as json

from .models import *  # noqa
from .queries import all_movies_without_actors_query


@pytest.mark.skip(reason='DB migrates before project is created')
def test_server(factory, sanic_server):
    factory.Movie.create_batch(5)
    request, response = sanic_server.sanic_app.test_client.post(
        '/graphql',
        data=json.dumps({'query': all_movies_without_actors_query})
    )
    assert response.json['errors'] is None
    assert len(response.json['data']['allMovies']) == 5
