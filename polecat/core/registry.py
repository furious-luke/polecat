import inspect
from operator import attrgetter

from polecat.utils import to_class
from polecat.utils.container import Option, OptionDict, passthrough

from .context import active_context

__all__ = ('RegistryMetaclass', 'Registry', 'MappedRegistry')

active_context().Meta.add_options(
    Option('registries', default=passthrough(OptionDict)())
)


class RegistryMetaclass(type):
    @classmethod
    def is_baseclass(cls, name, bases):
        return not (
            bases and
            name != getattr(bases[0], '_registry_base', None)
        )

    def __init__(cls, name, bases, dct):
        if not cls.is_baseclass(name, bases):
            active_context().registries[cls._registry].add(cls)
        super().__init__(name, bases, dct)


class Registry:
    def __init__(self, name, construct=False, name_mapper=None):
        self.name = name
        self.values = []
        self.construct = construct
        self.name_mapper = name_mapper or attrgetter('name')
        self.name_map = {}
        active_context().registries.Meta.add_options(
            Option(self.name, default=self)
        )

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.values[key]
        else:
            return self.name_map[key]

    def add(self, value):
        if self.construct:
            value = value()
        self.values.append(value)
        if self.name_mapper:
            self.name_map[self.name_mapper(value)] = value


class MappedRegistry(Registry):
    def __init__(self, name):
        super().__init__(name)
        self.values = {}

    def __getitem__(self, value):
        for base_class in inspect.getmro(to_class(value)):
            candidates = self.values.get(base_class)
            if candidates:
                for c in candidates:
                    match = getattr(c, 'match', None)
                    if not match or match(value):
                        return c
        raise KeyError(f'No {self.name} mapping for {value}')

    def add(self, mapped_value):
        for src in mapped_value.sources:
            self.values.setdefault(to_class(src), []).append(mapped_value)
