import pytest
from graphql_server.error import HttpQueryError
from polecat.project.project import Project
from polecat.rest.rest_api import RestAPI


def test_rest_api_match():
    project = Project()
    project.prepare()
    api = RestAPI(project)
    api.prepare()
    request = type('Request', (), {
        'method': 'GET',
        'path': '/rest/a'
    })
    event = type('Event', (), {
        'request': request,
        'session': None,
        'is_http': lambda: True
    })
    assert api.match(event) == True
    request = type('Request', (), {
        'method': 'GET',
        'path': '/graphql/a',
        'session': None
    })
    event = type('Event', (), {
        'request': request,
        'session': None,
        'is_http': lambda: True
    })
    assert api.match(event) == False


@pytest.mark.asyncio
async def test_rest_api_handle_event(db, factory):
    user = factory.User.create()
    project = Project()
    project.prepare()
    api = RestAPI(project)
    api.prepare()
    request = type('Request', (), {
        'method': 'GET',
        'path': '/rest/authenticate',
        'json': {
            'email': user.email,
            'password': user.password
        }
    })
    event = type('Event', (), {
        'request': request,
        'session': None,
        'is_http': lambda: True
    })
    response = await api.handle_event(event)
    assert response is not None


@pytest.mark.asyncio
async def test_rest_api_handle_event_not_found():
    project = Project()
    project.prepare()
    api = RestAPI(project)
    api.prepare()
    request = type('Request', (), {
        'method': 'GET',
        'path': '/rest/a'
    })
    event = type('Event', (), {
        'request': request,
        'session': None,
        'is_http': lambda: True
    })
    with pytest.raises(HttpQueryError):
        await api.handle_event(event)
