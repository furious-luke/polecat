from ..query import query as query_module
from .expression.update import Update
from .expression.select_ import Select
from .expression.where import Where
from .expression.subrelation_override import SubrelationOverride
from .insert_strategy import InsertStrategy


class UpdateStrategy(InsertStrategy):
    def parse_query(self, query):
        # TODO: Don't like this.
        if isinstance(query.source, query_module.Filter):
            relation = query.source.source
            where = Where(**query.source.options)
        else:
            relation = query.source
            where = None
        parsed_values = self.parse_values_or_subquery(query, query.values)
        if parsed_values and parsed_values.values.values[0]:
            expr = Update(
                relation,
                parsed_values,
                where=where
            )
        else:
            expr = Select(
                relation,
                where=where
            )
        if query.reverse_queries:
            expr = SubrelationOverride(expr, query.reverse_queries, self.root)
        return expr
