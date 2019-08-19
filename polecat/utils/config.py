import os

from .meta import MetaMetaclass
from .optiondict import OptionDict


class ConfigMetaclass(MetaMetaclass):
    def __new__(metaclass, name, bases, attrs):
        if name == 'Config':
            return type.__new__(metaclass, name, bases, attrs)
        return metaclass.build_dict_type(metaclass, name, attrs, ConfigDict)


class ConfigDict(OptionDict):
    def __init__(self, *args, prefix=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_prefix(prefix)

    def set_prefix(self, prefix):
        self.prefix = f'{prefix.upper()}' if prefix else ''
        if self.prefix and self.prefix[-1] != '_':
            self.prefix += '_'

    def get_default(self, option):
        key = f'{self.prefix}{option.key.upper()}'
        value = os.environ.get(key)
        if value is None:
            value = super().get_default(option)
        # TODO: Is this a problem?
        option.default = option.coerce(value)
        return option.default


class Config(metaclass=ConfigMetaclass):
    class Any:
        pass
