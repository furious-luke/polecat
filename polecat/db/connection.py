import os
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2


class ConnectionManager:
    def __init__(self):
        self.stack = [
            x
            for x in [os.environ.get('DATABASE_URL')]
            if x is not None
        ]
        self.connections = {}

    def get_url(self, url=None):
        try:
            return url or self.stack[-1]
        except IndexError:
            # TODO: Better exception.
            raise Exception('No database url specified')

    @contextmanager
    def connection(self, url=None, autocommit=True):
        url = self.get_url(url)
        conn = self.connections.get(url)
        if not conn:
            conn = self.open_connection(url, autocommit=autocommit)
        try:
            yield conn
            if not autocommit:
                conn.commit()
        except Exception:
            # TODO: Do I really need this?
            conn.rollback()
            raise

    @contextmanager
    def cursor(self, url=None, cursor=None, autocommit=True):
        # TODO: This conditional is ugly.
        if cursor:
            yield cursor
        else:
            with self.connection(url, autocommit=autocommit) as conn:
                curs = conn.cursor()
                try:
                    yield curs
                finally:
                    curs.close()

    def open_connection(self, url, autocommit=True):
        url = self.get_url(url)
        conn = psycopg2.connect(url)
        if autocommit:
            conn.autocommit = True
        self.connections[url] = conn
        return conn

    def close_all_connections(self):
        all_urls = list(self.connections.keys())
        for url in all_urls:
            self.close_connection(url)

    def close_connection(self, url):
        try:
            self.connections[url].close()
        except KeyError:
            pass
        try:
            del self.connections[url]
        except KeyError:
            pass

    @contextmanager
    def push_url(self, url):
        self.stack.append(url)
        try:
            yield
        finally:
            self.pop_url()

    def pop_url(self):
        url = self.stack.pop()
        self.close_connection(url)

    def parse_url(self, url=None):
        url = self.get_url(url)
        info = urlparse(url)
        return {
            'scheme': info.scheme,
            'dbname': info.path[1:],
            'host': info.hostname,
            'port': info.port,
            'username': info.username,
            'password': info.password
        }


manager = ConnectionManager()
connection = manager.connection
cursor = manager.cursor


@contextmanager
def transaction(cursor):
    cursor.execute('BEGIN')
    try:
        yield
        cursor.execute('COMMIT')
    finally:
        cursor.execute('ROLLBACK')
