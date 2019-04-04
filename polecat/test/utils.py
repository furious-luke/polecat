import os
from contextlib import contextmanager


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
