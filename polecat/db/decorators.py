from functools import wraps

from . import connection


def dbcursor(func):
    @wraps(func)
    def inner(*args, cursor=None, **kwargs):
        if cursor is None:
            with connection.cursor() as curs:
                return func(*args, cursor=curs, **kwargs)
        else:
            return func(*args, cursor=cursor, **kwargs)
    return inner
