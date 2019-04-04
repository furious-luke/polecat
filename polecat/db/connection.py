from contextlib import contextmanager

import psycopg2

from .utils import database_url


@contextmanager
def connection(url):
    conn = psycopg2.connect(database_url(url))
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def cursor(url=None):
    with connection(url) as conn:
        curs = conn.cursor()
        try:
            yield curs
        finally:
            curs.close()
