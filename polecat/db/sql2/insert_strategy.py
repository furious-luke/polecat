from ..query import Q
from ..query import query as query_module
from .expression.insert import Insert
from .expression.subquery import Subquery


class InsertStrategy:
    def __init__(self, root_strategy):
        self.root = root_strategy
        self.relation_counter = 0

    def parse_query(self, query):
        return Insert(
            query.source,
            self.parse_values_or_subquery(query.values),
            returning=self.root.current_select_columns
        )

    def parse_values_or_subquery(self, values_or_subquery):
        if isinstance(values_or_subquery, query_module.Values):
            return self.parse_values(values_or_subquery)
        else:
            return self.parse_subquery(values_or_subquery)

    def parse_values(self, values):
        parsed_values = {}
        for column_name, value in values.iter_items():
            if isinstance(value, (query_module.Query, Q)):
                value = self.parse_subquery(value)
            parsed_values[column_name] = value
        return parsed_values

    def parse_subquery(self, subquery):
        return Subquery(self.root.parse_queryable_or_builder(subquery))
