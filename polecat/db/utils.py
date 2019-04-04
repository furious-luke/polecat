import os
from contextlib import contextmanager
from urllib.parse import urlparse

database_url_stack = [os.environ['DATABASE_URL']]


@contextmanager
def push_database_url(url):
    global database_url_stack
    database_url_stack.append(url)
    try:
        yield
    finally:
        database_url_stack.pop()


def database_url(url=None):
    return url or database_url_stack[-1]


def parse_url(url=None):
    info = urlparse(database_url(url))
    return {
        'scheme': info.scheme,
        'dbname': info.path[1:],
        'host': info.hostname,
        'port': info.port,
        'username': info.username,
        'password': info.password
    }


def unparse_url(info):
    scheme = info['scheme']
    auth = info.get('username', '')
    if auth:
        password = info.get('password', None)
        if password:
            auth += f':{password}'
        auth += '@'
    host = info['host']
    dbname = info['dbname']
    return f'{scheme}://{auth}{host}/{dbname}'
