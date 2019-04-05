from contextlib import contextmanager
from traceback import print_tb


class EntityExists(Exception):
    pass


class EntityDoesNotExist(Exception):
    pass


class KnownError(Exception):
    pass


@contextmanager
def traceback():
    try:
        yield
    except Exception as e:
        print_tb(e.__traceback__)
        raise
