from functools import wraps

from ..utils.decorator import decorator_with_args
from . import connection


@decorator_with_args
def dbcursor(func, autocommit=True):
    @wraps(func)
    def inner(*args, cursor=None, **kwargs):
        if cursor is None:
            with connection.cursor(autocommit=autocommit) as curs:
                return func(*args, cursor=curs, **kwargs)
        else:
            # TODO: Make sure autocommit matches?
            return func(*args, cursor=cursor, **kwargs)
    return inner
