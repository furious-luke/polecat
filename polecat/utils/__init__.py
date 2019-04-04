import inspect
import random
import string


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


def to_tuple(value):
    if isinstance(value, (tuple, list)):
        return tuple(value)
    elif value is None:
        return ()
    else:
        return (value,)


def merge(target, source):
    for k, v in source.items():
        if isinstance(v, dict):
            merge(target.setdefault(k, {}), v)
        else:
            target[k] = v
    return target


def substitute(template, **kwargs):
    return string.Template(template).safe_substitute(kwargs)


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
