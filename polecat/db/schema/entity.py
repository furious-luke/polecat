from polecat.utils.repr import to_repr_attrs


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
            name: value
            for name, value in self.kwargs.items()
            if value is not None
        }

    def merge(self, *args, **kwargs):
        self.args += args
        self.kwargs.update(kwargs)
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
