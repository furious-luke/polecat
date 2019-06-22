from polecat.deploy.aws.event import LambdaEvent
from polecat.deploy.aws.middleware import DevelopMiddleware

host = 'hlzuceznbj.execute-api.ap-southeast-2.amazonaws.com'


def test_develop_middleware_no_trailing_slash():
    mw = DevelopMiddleware()
    event = LambdaEvent({
        'path': '/hello/world',
        'httpMethod': 'GET',
        'headers': {
            'Host': host
        }
    })
    mw.run(event)
    assert event.request.path == '/world'


def test_develop_middleware_with_trailing_slash():
    mw = DevelopMiddleware()
    event = LambdaEvent({
        'path': '/hello/world/',
        'httpMethod': 'GET',
        'headers': {
            'Host': host
        }
    })
    mw.run(event)
    assert event.request.path == '/world/'


def test_develop_middleware_no_match():
    mw = DevelopMiddleware()
    event = LambdaEvent({
        'path': '/hello/world/',
        'httpMethod': 'GET',
        'headers': {
            'Host': 'www.google.com'
        }
    })
    mw.run(event)
    assert event.request.path == '/hello/world/'
