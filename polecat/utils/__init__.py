import inspect
import random
import string
from pathlib import Path

from .retry import retry  # noqa
from .stringcase import snakecase


class Undefined:
    pass


def add_attribute(obj, key, value):
    setattr(obj, key, value)
    return obj


def random_ident(length=8):
    return ''.join(
        random.choices(string.ascii_lowercase, k=1) +
        random.choices(
            string.ascii_lowercase + string.digits,
            k=length
        )
    )


def to_class(value):
    return value if inspect.isclass(value) else value.__class__


def to_bool(value):
    if isinstance(value, str):
        return not (
            not len(value) or value.lower()[0] in ('f', 'n', '0')
        )
    else:
        return bool(value)


def get_class_path(value):
    return Path(inspect.getfile(value)).parent


def to_tuple(value):
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    elif value is None:
        return ()
    else:
        return (value,)


def to_list(value):
    # TODO: Meh, could be faster.
    return list(to_tuple(value))


def to_set(value):
    if isinstance(value, set):
        return value
    elif value is None:
        return set()
    else:
        return set(value)


def to_dict(value):
    if isinstance(value, None):
        return {}
    elif not isinstance(value, dict):
        return dict(value)
    else:
        return value


def merge(target, source):
    for k, v in source.items():
        if isinstance(v, dict):
            merge(target.setdefault(k, {}), v)
        else:
            target[k] = v
    return target


def substitute(template, **kwargs):
    return string.Template(template).safe_substitute(kwargs)


def capitalize(value):
    if value:
        return value[0].upper() + value[1:]
    else:
        return value


def uncapitalize(value):
    if value:
        return value[0].lower() + value[1:]
    else:
        return value


def get_path(source, path, separator='.'):
    parts = path.split(separator)
    value = source
    for part in parts:
        if value is not None:
            value = value.get(part)
    return value


def set_path(destination, path, value, separator='.'):
    parts = path.split(separator)
    for part in parts[:-1]:
        if part not in destination:
            destination[part] = {}
        destination = destination[part]
    destination[parts[-1]] = value


def get_data_dir():
    return Path(__file__).parent.parent / 'data'


def indent(text, size=4):
    return ('\n' + ' ' * size).join(text.split('\n'))


def name_from_class(cls, suffix=None):
    name = snakecase(to_class(cls).__name__)
    if suffix:
        pos = -len(suffix) - 1
        if name[pos:] == '_' + suffix:
            name = name[:pos]
    return name
