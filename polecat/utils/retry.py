import time
from functools import wraps

from .decorator import decorator_with_args


@decorator_with_args
def retry(func, max_retries=2, delay_ms=1000, swallow_error=False):
    @wraps(func)
    def inner(*args, **kwargs):
        cur_retry = 0
        while True:
            try:
                return func(*args, **kwargs)
            except Exception:
                if cur_retry == max_retries:
                    if swallow_error:
                        return
                    raise
                time.sleep(delay_ms/1000)
                cur_retry += 1
    return inner
