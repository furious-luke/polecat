from ..utils.stringcase import camelcase, snakecase

default_resolver = None


# TODO: Maybe move this elsewhere?
class Auto:
    pass


class Field:
    def __init__(self, resolver=None):
        self.resolver = resolver or default_resolver

    def __repr__(self):
        name = getattr(self, 'name', '?')
        return f'<{self.__class__.__name__} name="{name}">'

    def prepare(self, model):
        return self


class MutableField(Field):
    def __init__(self, *args, null=True, unique=False, default=None, primary_key=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.null = null
        self.unique = unique
        self.default = default
        self.primary_key = primary_key


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
    pass


class RelatedField(MutableField):
    def __init__(self, other, related_name=Auto, reverse=False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.other = other
        self.related_name = related_name
        self.reverse = reverse

    def prepare(self, model):
        self.add_related_field(model)
        return self

    def add_related_field(self, model):
        if self.related_name:
            related_name = self.make_related_name(
                self.related_name,
                model,
                self.other
            )
            if hasattr(self.other, related_name):
                # TODO: Better error.
                raise AttributeError('Related field name clash')
            # TODO: This whole process of adding an extra field to a
            # model is pretty awful. This should be handled somewhere
            # else.
            field = RelatedField(model, related_name=self.name, reverse=True)
            field.name = related_name  # TODO: Hmmm, not sure.
            field.cc_name = camelcase(related_name)
            self.other.Meta.fields[field.name] = field  # TODO: Ugh.
            self.other.Meta.cc_fields[field.cc_name] = field

    def make_related_name(self, related_name, from_model, to_model):
        if related_name == Auto:
            # TODO: Depends on `name` being added after model
            # construction, not sure I like that.
            # TODO: Better pluralize? Could do, but it's typically
            # expensive.
            return f'{snakecase(from_model.Meta.plural)}_by_{self.name}'
        else:
            return related_name


class ComputedField(Field):
    def __init__(self, function, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.function = function
