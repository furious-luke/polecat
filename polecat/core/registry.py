import inspect
from operator import attrgetter

from ..utils import to_class
from ..utils.container import OptionDict, passthrough
from .context import active_context

__all__ = ('RegistryMetaclass', 'Registry', 'MappedRegistry')

active_context().Meta.add_options(
    ('registries', passthrough(OptionDict)())
)


class RegistryMetaclass(type):
    def __init__(cls, name, bases, dct):
        if bases and name != getattr(cls, '_registry_base', name):
            active_context().registries[cls._registry].add(cls)
        super().__init__(name, bases, dct)


class Registry:
    def __init__(self, name, construct=False, mapper=None):
        self.name = name
        self.values = []
        self.construct = construct
        self.mapper = mapper or attrgetter('name')
        self.name_map = {}
        active_context().registries.Meta.add_options((self.name, self))

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
        if self.mapper:
            self.name_map[self.mapper(value)] = value


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
        raise KeyError(f'No {self.type} mapping for {value}')

    def add(self, mapped_value):
        for src in mapped_value.sources:
            self.values.setdefault(to_class(src), []).append(mapped_value)
