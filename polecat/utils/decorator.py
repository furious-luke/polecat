from functools import wraps


def decorator_with_args(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return func(args[0])
        else:
            return lambda f: func(f, *args, **kwargs)
    return inner
