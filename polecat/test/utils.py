import os
from contextlib import contextmanager

from polecat.db.connection import cursor, manager
from polecat.db.utils import unparse_url
from polecat.utils import random_ident


@contextmanager
def environ(**kwargs):
    orig = dict()
    todel = []
    try:
        for k, newval in kwargs.items():
            if k in os.environ:
                orig[k] = os.environ[k]
            else:
                todel.append(k)
            os.environ[k] = newval
        yield
    finally:
        for k, oldval in orig.items():
            os.environ[k] = oldval
        for k in todel:
            del os.environ[k]


@contextmanager
def create_database():
    dbinfo = manager.parse_url()
    test_dbname = random_ident()
    with cursor() as curs:
        curs.execute(f'create database {test_dbname}')
    try:
        test_url = unparse_url({**dbinfo, 'dbname': test_dbname})
        with manager.push_url(test_url):
            with cursor(test_url) as curs:
                yield curs
    finally:
        with cursor() as curs:
            curs.execute(f'drop database {test_dbname}')
