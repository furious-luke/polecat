from .passthrough import passthrough  # noqa


class Undefined:
    pass


class Option:
    def __init__(self, name, type=Undefined, default=Undefined):
        self.name = name
        self.default = default
        self.type = type


class OptionDict:
    """ A dictionary-like class in which all possible options are
    specified in advance. Allows for acknowledgement of incorrect
    accesses and suggestions for the correct key.
    """
    def __init__(self, options=None):
        self.options = set()
        self.items = {}
        self.types = {}
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
        self.items[key] = self.coerce(key, value)

    def coerce(self, key, value):
        if key in self.types:
            type = self.types[key]
            if type == bool:
                if isinstance(value, str):
                    return not (
                        not len(value) or value.lower()[0] in ('f', 'n', '0')
                    )
            value = type(value)
        return value

    def add_options(self, *options):
        keys_to_add = set()
        defaults_to_add = {}
        types_to_add = {}
        for opt in options:
            keys_to_add.add(opt.name)
            if opt.default != Undefined:
                defaults_to_add[opt.name] = opt.default
            if opt.type != Undefined:
                types_to_add[opt.name] = opt.type
        self.init_defaults(keys_to_add, defaults_to_add)
        self.options.update(keys_to_add)
        self.items.update(defaults_to_add)
        self.types.update(types_to_add)
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
        if closest:
            closest = min(closest, key=lambda x: x[0])[1]
            return KeyError(f'{key} not found, did you mean {closest}?')
        else:
            return KeyError(f'{key} not found')
