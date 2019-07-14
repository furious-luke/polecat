from polecat.utils.repr import to_repr_attrs

from .utils import Auto
from .variable import SessionVariable


class AsIs:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value


class ConstructionArguments:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        items = [repr(a) for a in self.args]
        items.append(to_repr_attrs(**self.filter_kwargs()))
        return ', '.join(items)

    def filter_kwargs(self):
        return {
            name: self.map_value(value)
            for name, value in self.kwargs.items()
            if value is not None
        }

    def map_value(self, value):
        if isinstance(value, SessionVariable):
            args = [repr(value.name)]
            if value.type:
                args.append(repr(value.type))
            args = ', '.join(args)
            return AsIs(f'schema.SessionVariable({args})')
        elif value == Auto:
            return AsIs('schema.Auto')
        else:
            return value

    def merge(self, *args, **kwargs):
        self.args += args
        self.kwargs.update({
            k: v
            for k, v in kwargs.items()
            if v is not None
        })
        return self


class Entity:
    def __eq__(self, other):
        return not self.has_changed(other)

    @property
    def dependencies(self):
        return self.get_dependent_entities()

    def get_dependent_entities(self):
        return ()

    def get_construction_arguments(self):
        return ConstructionArguments(args=None, kwargs=None)
