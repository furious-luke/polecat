import os

from .meta import MetaMetaclass
from .optiondict import OptionDict


class ConfigMetaclass(MetaMetaclass):
    def __new__(metaclass, name, bases, attrs):
        if name == 'Config':
            return type.__new__(metaclass, name, bases, attrs)
        return metaclass.build_dict_type(metaclass, name, attrs, ConfigDict)


class ConfigDict(OptionDict):
    def get_default(self, option):
        # TODO: Would like to make the prefix optional.
        value = os.environ.get(f'POLECAT_{option.key.upper()}')
        if value is None:
            value = super().get_default(option)
        # TODO: Is this a problem?
        option.default = option.coerce(value)
        return option.default


class Config(metaclass=ConfigMetaclass):
    class Any:
        pass
