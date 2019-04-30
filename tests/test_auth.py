from polecat.auth.jwt import jwt
from polecat.auth.middleware import RoleMiddleware
from polecat.deploy.event import HttpEvent

from .models import *  # noqa


# TODO: Where to put this?
class Request:
    def __init__(self, headers):
        self.headers = headers


def test_role_middleware():
    token = jwt({'role': 'default'})
    request = Request({
        'authorization': f'Bearer {token}'
    })
    event = HttpEvent({}, request)
    RoleMiddleware().run(event)
    assert event.claims is not None
    assert event.role == DefaultRole  # noqa
