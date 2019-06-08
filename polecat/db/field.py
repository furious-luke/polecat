import inspect

from psycopg2.sql import SQL, Identifier

from ..model import field as mf
from ..utils.predicates import not_empty

__all__ = (
    'db_field_registry', 'get_db_field',
    'TextField', 'IntField',
    'RelatedField'
)

db_field_registry = {
}


def get_db_field(field):
    # TODO: Could cache the results against the source field?
    for base_class in inspect.getmro(field.__class__):
        candidates = db_field_registry.get(base_class)
        if candidates:
            for c in candidates:
                if c.match(field):
                    return c(field)
    raise Exception(f'unknown database field type {field}')


class FieldMetaclass(type):
    def __init__(cls, name, bases, dct):
        if bases and name != 'Field':
            for src in getattr(cls, 'sources', ()):
                db_field_registry.setdefault(src, []).append(cls)
        super().__init__(name, bases, dct)


class Field(metaclass=FieldMetaclass):
    db_type = None
    sources = ()

    @classmethod
    def match(cls, field):
        return True

    def __init__(self, source):
        self.source = source

    @property
    def name(self):
        return self.source.name

    @property
    def type(self):
        return self.db_type

    @property
    def unique(self):
        return self.source.unique

    @property
    def null(self):
        return self.source.null

    @property
    def primary_key(self):
        return getattr(self.source, 'primary_key', None)

    def is_concrete(self):
        return True

    def get_value(self, model):
        return getattr(model, self.name, None)

    def get_create_sql(self):
        return SQL(' ').join(filter(not_empty, (
            Identifier(self.name),
            self.get_type_sql(),
            self.get_constraints_sql()
        )))

    def get_type_sql(self):
        return SQL(self.type)

    def get_constraints_sql(self, extra=()):
        src = self.source
        elems = tuple(filter(not_empty, (
            SQL('NOT NULL') if not src.null else None,
            SQL('UNIQUE') if src.unique else None,
            SQL('DEFAULT {}').format(self.translate_default(src.default))
            if src.default is not None else None,
            *extra
        )))
        if not elems:
            return None
        return SQL(' ').join(elems)

    def translate_default(self, default):
        return default


class TextField(Field):
    db_type = 'text'
    sources = (mf.TextField,)

    @property
    def type(self):
        if self.length:
            # TODO: Validate length.
            return f'varchar({self.length})'
        else:
            return super().type

    @property
    def length(self):
        return self.source.length


class IntField(Field):
    db_type = 'int'
    sources = (mf.IntField,)

    @property
    def type(self):
        if self.primary_key:
            return 'serial'
        else:
            return super().type

    def get_constraints_sql(self, extra=()):
        return super().get_constraints_sql((
            SQL('PRIMARY KEY') if self.primary_key else None,
            *extra
        ))


class PasswordField(TextField):
    db_type = 'chkpass'
    sources = (mf.PasswordField,)


class UUIDField(Field):
    db_type = 'uuid'
    sources = (mf.UUIDField,)

    def translate_default(self, default):
        if self.auto:
            return 'uuid_generate_v4()'
        else:
            return default


class PointField(Field):
    db_type = 'point'
    sources = (mf.PointField,)


class DatetimeField(Field):
    db_type = 'timestamptz'
    sources = (mf.DatetimeField,)


class RelatedField(IntField):
    sources = (mf.RelatedField,)

    @property
    def references(self):
        other_table = self.source.other.Meta.table_name
        result = f'{other_table}.id'
        app = self.source.other.Meta.app
        if app:
            result = f'{app.name}.{result}'
        return result

    # def get_other(self):
    #     # TODO: Cache this?
    #     return get_db_field(self.source.other)

    # def get_type_sql(self):
    #     return self.get_other().get_type_sql()

    def get_value(self, model):
        value = super().get_value(model)
        if value:
            # TODO: Shouldn't be named `id`, should be whatever the
            # linked field is. Also, how to handle an integer or
            # whatever value the PK is?
            value = value.id
        return value

    def get_constraints_sql(self):
        other_table = self.source.other.Meta.table_name
        return super().get_constraints_sql((
            SQL('REFERENCES {}(id)').format(Identifier(other_table)),
        ))


class ReverseField(IntField):
    sources = (mf.ReverseField,)

    def is_concrete(self):
        return False
