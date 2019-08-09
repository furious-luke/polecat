from . import to_tuple
from .optiondict import Option, OptionDict
from .passthrough import passthrough


class MetaMetaclass(type):
    def __new__(metaclass, name, bases, attrs):
        if name == 'Meta':
            return super().__new__(metaclass, name, bases, attrs)
        return metaclass.build_dict_type(metaclass, name, attrs)

    def build_dict_type(metaclass, name, attrs, base=OptionDict):
        cls = super().__new__(metaclass, name, (base,), attrs)
        cls.initial_options = build_options(attrs)
        return passthrough(cls)


def build_options(attrs):
    options = {}
    for key, option in attrs.items():
        if key.startswith('__'):
            continue
        if not isinstance(option, Option):
            args = (key,) + to_tuple(option)
            option = Option.factory(*args)
        else:
            option.key = key
        options[option.key] = option
    return options


class Meta(metaclass=MetaMetaclass):
    class Any:
        pass
