import time
from contextlib import contextmanager


@contextmanager
def retry(max_retries=3, delay_ms=1000):
    while True:
        try:
            yield
        except Exception:
            if max_retries <= 0:
                raise
            time.sleep(delay_ms/1000)
            max_retries -= 1
