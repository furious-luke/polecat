import os
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2


class ConnectionManager:
    def __init__(self):
        # TODO: This should be transferred to POLECAT_DATABASE_URL
        # from the config.
        self.stack = [
            x
            for x in [os.environ.get('DATABASE_URL')]
            if x is not None
        ]
        self.connections = {}
        self.current_cursor = {}

    def get_url(self, url=None):
        try:
            return url or self.stack[-1]
        except IndexError:
            # TODO: Better exception.
            raise Exception('No database url specified')

    # TODO: autocommit really doesn't make sense here for the
    # manager. It needs to be in the __init__ method, as the
    # connection gets retained across calls.
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
        url = self.get_url(url)
        curs = self.current_cursor.get(url)
        if curs:
            yield curs
        else:
            with self.connection(url, autocommit=autocommit) as conn:
                curs = conn.cursor()
                self.current_cursor[url] = curs
                try:
                    yield curs
                finally:
                    curs.close()
                    del self.current_cursor[url]

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
def transaction(curs=None):
    # TODO: Not super happy about how manual the BEGIN and COMMIT
    # calls are. Performance hit?
    if curs is None:
        with cursor() as curs:
            try:
                curs.execute('BEGIN')
                yield curs
                curs.execute('COMMIT')
            except Exception:
                curs.execute('ROLLBACK')
                raise
    else:
        try:
            curs.execute('BEGIN')
            yield curs
            curs.execute('COMMIT')
        except Exception:
            curs.execute('ROLLBACK')
            raise
