from . import to_class


def to_repr(name, **attrs):
    name = to_repr_name(name)
    attrs_str = to_repr_attrs(attrs)
    return f'<{name}{prespace(attrs_str)}>'


def to_repr_name(name):
    if not isinstance(name, str):
        name = to_class(name).__name__
    return name


def to_repr_attrs(**attrs):
    return ', '.join([
        f'{name}={repr(value)}'
        for name, value in attrs.items()
    ])


def prespace(string):
    return (' ' if string else '') + string
