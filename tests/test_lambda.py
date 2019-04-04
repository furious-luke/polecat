import ujson as json

from .models import *  # noqa
from .queries import all_movies_query


def test_server(db, factory, lambda_server):
    factory.Movie.create_batch(5)
    response = lambda_server.handle({
        'httpMethod': 'POST',
        'path': '/graphql',
        'body': json.dumps({'query': all_movies_query})
    })
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    assert data['errors'] is None
    assert len(data['data']['allMovies']) == 5
