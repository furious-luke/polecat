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
def cursor(url=None, cursor=None, **kwargs):
    # TODO: This conditional is ugly.
    if cursor:
        yield cursor
    else:
        with connection(url, **kwargs) as conn:
            curs = conn.cursor()
            try:
                yield curs
            finally:
                curs.close()



@contextmanager
def transaction(cursor):
    cursor.execute('BEGIN')
    try:
        yield
        cursor.execute('COMMIT')
    finally:
        cursor.execute('ROLLBACK')
