from collections import OrderedDict


class SingleDict(OrderedDict):
    def __setitem__(self, key, value):
        if key in self:
            raise KeyError(f'Duplicate key "{key}"')
        super().__setitem__(key, value)
