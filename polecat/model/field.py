from polecat.db.schema.utils import Auto

from ..utils.stringcase import camelcase, snakecase
from .exceptions import InvalidModelDataError

default_resolver = None


class Field:
    def __init__(self, resolver=None, omit=None):
        self.resolver = resolver or default_resolver
        self.omit = omit or 0

    def __repr__(self):
        name = getattr(self, 'name', '?')
        return f'<{self.__class__.__name__} name="{name}">'

    def prepare(self, model):
        return self

    def use_get_query(self):
        return False

    def from_incoming(self, instance, value):
        return value

    def to_outgoing(self, instance, value):
        return value


class MutableField(Field):
    def __init__(self, *args, null=True, unique=False, default=None,
                 primary_key=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.null = null
        self.unique = unique
        self.default = default
        self.primary_key = primary_key

    def use_get_query(self):
        return self.primary_key or self.unique


class TextField(MutableField):
    def __init__(self, *args, length=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = length


class EmailField(TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, length=255, **kwargs)


class PhoneField(TextField):
    pass


class PasswordField(TextField):
    pass


class BoolField(MutableField):
    pass


class IntField(MutableField):
    pass


class SerialField(MutableField):
    pass


class FloatField(MutableField):
    pass


class DatetimeField(MutableField):
    pass


class UUIDField(MutableField):
    def __init__(self, *args, auto=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto = auto


class PointField(MutableField):
    pass


class GCSPointField(PointField):
    pass


class ReverseField(Field):
    def __init__(self, other, related_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.other = other
        self.related_name = related_name

    def from_incoming(self, instance, value):
        return [
            self.other(**{self.related_name: instance, **v})
            for v in value
        ]

    def to_outgoing(self, instance, value):
        return [
            self._model_to_dict(v)
            for v in (value or [])
        ]

    def _model_to_dict(self, model):
        # TODO: Ugh, no. Must fix.
        values = {}
        for field_name, field in model.Meta.fields.items():
            if not hasattr(model, field_name):
                continue
            if field_name == self.related_name:
                continue
            values[field_name] = field.to_outgoing(
                model,
                getattr(model, field_name)
            )
        return values


class RelatedField(MutableField):
    def __init__(self, other, related_name=Auto, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.other = other
        self.related_name = related_name

    def prepare(self, model):
        if self.other == 'self':
            self.other = model
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
            field = ReverseField(model, related_name=self.name)
            field.name = related_name  # TODO: Hmmm, not sure.
            field.cc_name = camelcase(related_name)
            self.other.Meta.fields[field.name] = field  # TODO: Ugh.
            self.other.Meta.cc_fields[field.cc_name] = field
            # TODO: Potentially information losing: now we don't know
            # that Auto was originally set.
            self.related_name = related_name

    def make_related_name(self, related_name, from_model, to_model):
        if related_name == Auto:
            # TODO: Depends on `name` being added after model
            # construction, not sure I like that.
            # TODO: Better pluralize? Could do, but it's typically
            # expensive.
            return f'{snakecase(from_model.Meta.plural)}_by_{self.name}'
        else:
            return related_name

    def from_incoming(self, instance, value):
        if isinstance(value, self.other):
            return value
        else:
            try:
                value = {'id': int(value)}
            except TypeError:
                pass
            try:
                return self.other(**value)
            except TypeError:
                raise InvalidModelDataError(self.other, value)

    def to_outgoing(self, instance, value):
        from .model import Model
        if isinstance(value, Model):
            if getattr(value, 'id', None) is not None:
                value = value.id
            else:
                value = self._model_to_dict(value)
        return value

    def _model_to_dict(self, model):
        # TODO: Ugh, no. Must fix.
        values = {}
        for field_name, field in model.Meta.fields.items():
            if not hasattr(model, field_name):
                continue
            if field_name == self.related_name:
                continue
            values[field_name] = field.to_outgoing(
                model,
                getattr(model, field_name)
            )
        return values


class ComputedField(Field):
    def __init__(self, function, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.function = function
