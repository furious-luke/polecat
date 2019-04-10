from psycopg2.sql import SQL, Identifier

from ...model.field import ReverseField
from ..field import get_db_field


class Insert:
    @classmethod
    def evaluate(self, query):
        model = query.model
        (
            field_names_sql,
            field_values_sql,
            field_values,
            returning
        ) = self.get_values_sql(query, model)
        return (
            SQL('INSERT INTO {} ({}) VALUES {} RETURNING {}').format(
                Identifier(model.Meta.table),
                field_names_sql,
                field_values_sql,
                returning
            ),
            tuple(field_values)  # TODO: Avoid conversion?
        )

    @classmethod
    def get_values_sql(self, query, model):
        field_names, field_values, returning = self.get_values(model)
        # TODO: Should skip this if no selector?
        returning = set(returning).union(query.selector.all_fields())
        return (
            SQL(',').join(map(Identifier, field_names)),
            SQL('(' + ','.join(('%s',) * len(field_names)) + ')'),
            field_values,
            SQL(',').join(map(Identifier, returning))
        )

    @classmethod
    def get_values(self, model):
        # TODO: Make this more functional.
        field_names = []
        field_values = []
        returning = []
        for field in model.Meta.fields.values():
            # TODO: This should be auto fields, not primary key.
            if getattr(field, 'primary_key', None):
                returning.append(field.name)
                continue
            # TODO: Could probably collect mutable fields onto models,
            # making this redundant.
            if isinstance(field, ReverseField):
                continue
            fn, fv = self.get_value_for_field(model, field)
            field_names.append(fn)
            field_values.append(fv)
        return (field_names, field_values, returning)

    @classmethod
    def get_value_for_field(self, model, field):
        return (field.name, get_db_field(field).get_value(model))
