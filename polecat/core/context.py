from functools import wraps

from ..utils.container import OptionDict

global_context = OptionDict()


def active_context(*args):
    global global_context
    if len(args):
        func = args[0]
        @wraps(func)
        def inner(*args, **kwargs):
            return func(*args, context=global_context, **kwargs)
        return inner
    return global_context
