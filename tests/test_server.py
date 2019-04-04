import ujson as json

from .models import *  # noqa
from .queries import all_movies_query


def test_server(db, factory, server):
    factory.Movie.create_batch(5)
    request, response = server.sanic_app.test_client.post(
        '/graphql',
        data=json.dumps({'query': all_movies_query})
    )
    assert response.json['errors'] is None
    assert len(response.json['data']['allMovies']) == 5
