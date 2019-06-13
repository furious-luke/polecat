from . import to_class


def to_repr(tag, **attrs):
    tag = to_repr_tag(tag)
    attrs_str = to_repr_attrs(**attrs)
    return f'<{tag}{prespace(attrs_str)}>'


def to_repr_tag(tag):
    if not isinstance(tag, str):
        tag = to_class(tag).__name__
    return tag


def to_repr_attrs(**attrs):
    return ', '.join([
        f'{name}={repr(value)}'
        for name, value in attrs.items()
    ])


def prespace(string):
    return (' ' if string else '') + string
