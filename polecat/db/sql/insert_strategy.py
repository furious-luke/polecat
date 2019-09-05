from ..query import query as query_module
from .expression.insert import Insert
from .expression.subquery import Subquery
from .expression.subrelation_override import SubrelationOverride
from .expression.values import Values


class InsertStrategy:
    def __init__(self, root_strategy):
        self.root = root_strategy
        self.relation_counter = 0

    def parse_query(self, query):
        expr = Insert(
            query.source,
            self.parse_values_or_subquery(query, query.values)
        )
        if query.reverse_queries:
            expr = SubrelationOverride(expr, query.reverse_queries, self.root)
        return expr

    def parse_values_or_subquery(self, query, values_or_subquery):
        if isinstance(values_or_subquery, query_module.Values):
            return self.parse_values(query, values_or_subquery)
        else:
            return self.parse_subquery(values_or_subquery)

    def parse_values(self, query, values):
        parsed_values = []
        for row in values.iter_rows():
            row_values = []
            for _, value in row:
                if isinstance(value, query_module.Query):
                    value = self.parse_subquery(value)
                row_values.append(value)
            parsed_values.append(row_values)
        # TODO: Forced override.
        values.values = parsed_values
        return Values(values, query.source)

    def parse_subquery(self, subquery):
        if self.should_add_select(subquery):
            subquery = query_module.Select(
                subquery,
                query_module.Selection('id')
            )
        return Subquery(self.root.parse_queryable_or_builder(subquery))

    def should_add_select(self, subquery):
        return isinstance(subquery, (query_module.Insert, query_module.Update))
