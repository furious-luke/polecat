from psycopg2.sql import SQL, Identifier

from ...utils import to_class
from ..connection import cursor
from ..field import get_db_field
from .query import Query


# TODO: Should probably just use query.Query?
class Q:
    def __init__(self, model):
        self.model_class = to_class(model)
        self.model = model

    def select(self, *fields, **lookups):
        return Query(self.model_class).select(*fields, **lookups)

    def get(self, *args, **kwargs):
        return Query(self.model_class).get(*args, **kwargs)

    def insert(self):
        with cursor() as curs:
            curs.execute(*self.get_insert_sql())
            result = curs.fetchone()
            self.model.id = result[0]

    def get_insert_sql(self):
        (
            field_names_sql,
            field_values_sql,
            field_values,
            returning
        ) = self.get_insert_values_sql()
        return (
            SQL('INSERT INTO {} ({}) VALUES {} RETURNING {}').format(
                Identifier(self.model_class.Meta.table),
                field_names_sql,
                field_values_sql,
                returning
            ),
            field_values
        )

    def get_insert_values_sql(self):
        field_names, field_values, returning = self.get_insert_values()
        return (
            SQL(',').join(map(Identifier, field_names)),
            SQL('(' + ','.join(('%s',) * len(field_names)) + ')'),
            field_values,
            SQL(',').join(map(Identifier, returning))
        )

    def get_insert_values(self):
        # TODO: Make this more functional.
        field_names = []
        field_values = []
        returning = []
        for field in self.model_class.Meta.fields.values():
            # TODO: This should be auto fields, not primary key.
            if getattr(field, 'primary_key', None):
                returning.append(field.name)
                continue
            fn, fv = self.get_value_for_field(field)
            field_names.append(fn)
            field_values.append(fv)
        return (field_names, field_values, returning)

    def get_value_for_field(self, field):
        return (field.name, get_db_field(field).get_value(self.model))
