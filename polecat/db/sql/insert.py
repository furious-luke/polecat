from psycopg2.sql import SQL, Composed, Identifier

from ...model.field import ReverseField
from ..field import get_db_field
from .cte import CTE


class Insert:
    @classmethod
    def evaluate(self, model, selector=None, before=None, nesting=None):
        (
            field_names_sql,
            field_values_sql,
            field_values,
            returning
        ) = self.get_values_sql(model, selector, nesting)
        cte = CTE(
            SQL('INSERT INTO {} ({}) VALUES {} RETURNING {}').format(
                Identifier(model.Meta.table),
                field_names_sql,
                field_values_sql,
                returning
            ),
            tuple(field_values),  # TODO: Avoid conversion?,
            before=before
        )
        prev_cte = cte
        for field in model.Meta.fields.values():
            # TODO: Inefficient.
            if not isinstance(field, ReverseField):
                continue
            fn, fv = self.get_value_for_field(model, field)
            if not fv:
                continue
            for sub_model in fv:
                prev_cte = self.evaluate(sub_model, before=prev_cte, nesting={field.related_name: cte})
        return cte

    @classmethod
    def get_values_sql(self, model, selector=None, nesting=None):
        field_names, field_values, returning = self.get_values(model, nesting)
        # TODO: Should skip this if no selector?
        if selector:
            returning = set(returning).union(selector.all_fields())
            # TODO: There has got to be a better way...
            returning = [f for f in returning if not isinstance(model.Meta.fields[f], ReverseField)]
        # TODO: This is pretty inefficient.
        return (
            SQL(',').join(map(Identifier, field_names)),
            SQL('(' + ','.join('{}' if isinstance(fv, Composed) else '%s' for fv in field_values) + ')').format(
                *tuple(fv for fv in field_values if isinstance(fv, Composed))
            ),
            tuple(fv for fv in field_values if not isinstance(fv, Composed)),
            SQL(',').join(map(Identifier, returning))
        )

    @classmethod
    def get_values(self, model, nesting=None):
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
            # Don't generate for nested fields.
            if nesting and field.name in nesting:
                continue
            if hasattr(model, field.name):
                fn, fv = self.get_value_for_field(model, field)
                field_names.append(fn)
                field_values.append(fv)
        if nesting:
            for fn, cte in nesting.items():
                # TODO: Confirm name doesn't already appear?
                field_names.append(fn)
                field_values.append(SQL('(SELECT id FROM {})').format(
                    Identifier(cte.alias)
                ))
        return (field_names, field_values, returning)

    @classmethod
    def get_value_for_field(self, model, field):
        # TODO: Improve efficiency?
        db_field = get_db_field(field)
        return (field.name, db_field.get_value(model))
