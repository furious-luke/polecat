from . import to_tuple


def passthrough(cls):
    class Wrapper:
        def __init__(self, *args, **kwargs):
            self.__dict__['Meta'] = self.Meta(*args, **kwargs)

        def __getattr__(self, key):
            return self.Meta.get(key)

        def __setattr__(self, key, value):
            return self.Meta.set(key, value)

        def __getitem__(self, key):
            return self.Meta.get(key)

        def __setitem__(self, key, value):
            return self.Meta.set(key, value)

    Wrapper.__qualname__ = Wrapper.__name__ = cls.__name__
    cls.__qualname__ = cls.__name__ = 'Meta'
    Wrapper.Meta = cls
    return Wrapper


class OptionDict:
    def __init__(self, options=None):
        self.options = set()
        self.items = {}
        self.add_options(*(options or ()))

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def get(self, key):
        try:
            return self.items[key]
        except KeyError:
            pass
        if key not in self.options:
            raise self.key_error(key)
        raise ValueError(f'No value set for key {key}')

    def set(self, key, value):
        if key not in self.options:
            raise self.key_error(key)
        self.items[key] = value

    def add_options(self, *options):
        keys_to_add = set()
        defaults_to_add = {}
        for opt in options:
            opt = to_tuple(opt)
            if len(opt) not in (2, 1):
                raise ValueError('Invalid tuple size for OptionDict')
            keys_to_add.add(opt[0])
            if len(opt) == 2:
                defaults_to_add[opt[0]] = opt[1]
        self.init_defaults(keys_to_add, defaults_to_add)
        self.options.update(keys_to_add)
        self.items.update(defaults_to_add)
        return self

    def init_defaults(self, keys_to_add, defaults_to_add):
        pass

    def remove_options(self, *options):
        for opt in options:
            try:
                self.options.remove(opt)
            except KeyError:
                pass
            try:
                del self.items[opt]
            except KeyError:
                pass
        return self

    def key_error(self, key):
        try:
            from Levenshtein import distance
        except ImportError:
            return KeyError(f'{key} not found')
        closest = [
            (distance(key, opt), opt)
            for opt in self.options
        ]
        closest = min(closest, key=lambda x: x[0])[1]
        return KeyError(f'{key} not found, did you mean {closest}?')
