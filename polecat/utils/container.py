from . import to_tuple


class OptionDict:
    def __init__(self):
        self.__dict__['_options'] = set()
        self.__dict__['_items'] = {}

    def __getitem__(self, key):
        return self._get(key)

    def __getattr__(self, key):
        return self._get(key)

    def __setitem__(self, key, value):
        return self._set(key, value)

    def __setattr__(self, key, value):
        return self._set(key, value)

    def _get(self, key):
        if key not in self._options:
            raise self._key_error(key)
        try:
            return self._items[key]
        except KeyError:
            pass
        raise ValueError(f'No value set for key {key}')

    def _set(self, key, value):
        if key not in self._options:
            raise self._key_error(key)
        self._items[key] = value

    def _add_options(self, *options):
        keys_to_add = set()
        defaults_to_add = {}
        for opt in options:
            opt = to_tuple(opt)
            if len(opt) not in (2, 1):
                raise ValueError('Invalid tuple size for OptionDict')
            keys_to_add.add(opt[0])
            if len(opt) == 2:
                defaults_to_add[opt[0]] = opt[1]
        self.__dict__['_options'].update(keys_to_add)
        self.__dict__['_items'].update(defaults_to_add)
        return self

    def _remove_options(self, *options):
        for opt in options:
            try:
                self._options.remove(opt)
            except KeyError:
                pass
            try:
                del self._items[opt]
            except KeyError:
                pass
        return self

    def _key_error(self, key):
        try:
            from Levenshtein import distance
        except ImportError:
            return KeyError(f'{key} not found')
        closest = [
            (distance(key, opt), opt)
            for opt in self._options
        ]
        closest = min(closest, key=lambda x: x[0])[1]
        return KeyError(f'{key} not found, did you mean {closest}?')
