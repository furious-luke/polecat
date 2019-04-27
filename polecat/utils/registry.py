import inspect

from . import to_class


class RegistryMetaclass(type):
    def __init__(cls, name, bases, dct):
        if bases and name != getattr(cls, '_registry_base', name):
            cls._registry.add(cls)
        super().__init__(name, bases, dct)


class Registry:
    def __init__(self, type=None, construct=False, mapper=None):
        self.type = type or 'registry'
        self.values = []
        self.construct = construct
        self.mapper = mapper
        self.map = {}

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, index):
        return self.values[index]

    def add(self, value):
        if self.construct:
            value = value()
        self.values.append(value)
        if self.mapper:
            self.map[self.mapper(value)] = value


class MappedRegistry(Registry):
    def __init__(self, type=None):
        super().__init__(type)
        self.values = {}

    def __getitem__(self, value):
        for base_class in inspect.getmro(self.to_class(value)):
            candidates = self.values.get(base_class)
            if candidates:
                for c in candidates:
                    match = getattr(c, 'match', None)
                    if not match or match(value):
                        return c
        raise KeyError(f'no {self.type} mapping for {value}')

    def add(self, mapped_value):
        for src in self.get_sources(mapped_value):
            self.values.setdefault(self.to_class(src), []).append(mapped_value)

    def get_sources(self, mapped_value):
        return mapped_value.sources

    def to_class(self, value):
        return to_class(value)
