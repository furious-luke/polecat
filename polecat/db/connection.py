from contextlib import contextmanager

import psycopg2

from .utils import database_url


@contextmanager
def connection(url, autocommit=True):
    conn = psycopg2.connect(database_url(url))
    if autocommit:
        conn.autocommit = True
    try:
        yield conn
        if not autocommit:
            conn.commit()
    finally:
        conn.close()


@contextmanager
def cursor(url=None, **kwargs):
    with connection(url, **kwargs) as conn:
        curs = conn.cursor()
        try:
            yield curs
        finally:
            curs.close()
