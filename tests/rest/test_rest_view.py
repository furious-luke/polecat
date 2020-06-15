from polecat.rest.schema import RestView

from ..models import Authenticate


def test_rest_view(db, factory):
    user = factory.User.create()
    view = RestView(Authenticate)
    request = type('Request', (), {
        'path': '/a',
        'session': None,
        'json': {
            'email': user.email,
            'password': user.password
        }
    })
    event = type('Event', (), {
        'request': request
    })
    response = view.resolve(request, context_value={
        'event': event
    })
    assert response is not None
    assert response.get('token') is not None
