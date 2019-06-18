from ..query import query as query_module
from .expression.update import Update
from .expression.where import Where
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
        return Update(
            relation,
            self.parse_values_or_subquery(query, query.values),
            where=where
        )
