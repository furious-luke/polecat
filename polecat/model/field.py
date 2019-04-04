default_resolver = None


class Field:
    def __init__(self, resolver=None):
        self.resolver = resolver or default_resolver

    def __repr__(self):
        name = getattr(self, 'name', '?')
        return f'<{self.__class__.__name__} name="{name}">'


class MutableField(Field):
    def __init__(self, *args, null=True, unique=False, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.null = null
        self.unique = unique
        self.default = default


class TextField(MutableField):
    def __init__(self, *args, length=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = length


class EmailField(TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, length=255, **kwargs)


class PasswordField(TextField):
    pass


class IntField(MutableField):
    def __init__(self, *args, primary_key=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_key = primary_key


class RelatedField(MutableField):
    def __init__(self, other, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.other = other


class ComputedField(Field):
    def __init__(self, function, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.function = function
