from psycopg2.sql import SQL, Identifier

from ...model.field import ReverseField
from .cte import CTE
from .insert import Insert


class Update(Insert):
    @classmethod
    def evaluate(self, model, selector=None, before=None, nesting=None):
        # TODO: Must have an id.
        (
            field_names_sql,
            field_values_sql,
            field_values,
            returning
        ) = self.get_values_sql(model, selector, nesting)
        cte = CTE(
            SQL('UPDATE {} SET ({}) = ROW{} WHERE id = %s RETURNING {}').format(
                Identifier(model.Meta.table_name),
                field_names_sql,
                field_values_sql,
                returning
            ),
            tuple(field_values) + (model.id,),  # TODO: Avoid conversion?,
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
