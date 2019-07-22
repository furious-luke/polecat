from polecat.utils import Undefined, to_dict, to_list


class UndefinedOptionError(Exception):
    pass


class DuplicateOptionError(Exception):
    pass


class OptionDict:
    """ A dictionary-like class in which all possible options are
    specified in advance. Allows for acknowledgement of incorrect
    accesses and suggestions for the correct key.
    """
    def __init__(self, options=None):
        self.options = {**getattr(self, 'initial_options', {})}
        self.values = {}
        self.add_options(*(options or ()))

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def add_options(self, *options):
        for opt in options:
            if opt.key in self.options:
                raise DuplicateOptionError(f'{opt.key} already exists')
            self.options[opt.key] = opt
        return self

    def get(self, key):
        try:
            return self.get_option(key).get(self)
        except UndefinedOptionError:
            return self.handle_undefined(key)

    def set(self, key, value):
        self.get_option(key).set(self, value)

    def get_option(self, key):
        try:
            return self.options[key]
        except KeyError:
            raise self.key_error(key)

    def handle_undefined(self, key):
        raise

    def merge(self, other):
        for key, value in other.items():
            self.get_option(key).merge(self, value)

    def merge_from_type(self, other):
        for option in self.options.values():
            option.merge_from_type(self, other)

    def items(self):
        for key, option in self.options.values():
            yield key, option.get()

    def remove_options(self, *options):
        for opt in options:
            try:
                del self.options[opt]
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


class OptionMetaclass(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        type = getattr(cls, 'TYPE', None)
        if type is not None:
            cls.TYPE_MAP[type] = cls


class Option(metaclass=OptionMetaclass):
    TYPE_MAP = {}

    @staticmethod
    def factory(option_or_key, type=None, default=Undefined):
        if isinstance(option_or_key, Option):
            return option_or_key
        option_class = Option.TYPE_MAP.get(type, Option)
        return option_class(option_or_key, default=default)

    def __init__(self, key=None, default=Undefined):
        self.key = key
        self.default = default

    def get(self, obj):
        value = self.get_value(obj)
        if value is Undefined:
            if self.default is Undefined:
                raise UndefinedOptionError(f'{self.key} is undefined')
            return self.default
        return value

    def set(self, obj, value):
        self.set_value(obj, self.coerce(value))

    def get_value(self, obj):
        return obj.values.get(self.key, Undefined)

    def set_value(self, obj, value):
        obj.values[self.key] = value

    def coerce(self, value):
        return value

    def merge(self, obj, other):
        self.set(obj, other)

    def merge_from_type(self, obj, other):
        value = getattr(other, self.key, Undefined)
        if value is not Undefined:
            self.merge(obj, value)


class IntOption(Option):
    TYPE = int

    def coerce(self, value):
        return int(value)


class StrOption(Option):
    TYPE = str

    def coerce(self, value):
        return str(value)


class BoolOption(Option):
    TYPE = bool

    def coerce(self, value):
        if isinstance(value, str):
            return not (
                not len(value) or value.lower()[0] in ('f', 'n', '0')
            )
        else:
            return bool(value)


class ListOption(Option):
    TYPE = list

    def coerce(self, value):
        return to_list(value)

    def merge(self, obj, other):
        return self.get_value(obj).extend(self.coerce(other))


class DictOption(Option):
    TYPE = dict

    def coerce(self, value):
        return to_dict(value)

    def merge(self, obj, other):
        return self.get_value(obj).merge(self.coerce(other))
