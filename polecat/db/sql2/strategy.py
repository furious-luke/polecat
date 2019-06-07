from ..query import Q
from ..query import query as query_module
from .delete_strategy import DeleteStrategy
from .expression.alias import Alias
from .expression.cte import CTE
from .insert_strategy import InsertStrategy
from .select_strategy import SelectStrategy
from .update_strategy import UpdateStrategy


class Strategy:
    def __init__(self):
        self.select_strategy = SelectStrategy(self)
        self.insert_strategy = InsertStrategy(self)
        self.update_strategy = UpdateStrategy(self)
        self.delete_strategy = DeleteStrategy(self)

    def parse(self, queryable_or_builder):
        self.cte = CTE()
        self.query_alias_map = {}
        expr = self.parse_queryable_or_builder(queryable_or_builder)
        self.cte.set_final_expression(expr)
        return self.cte

    def parse_queryable_or_builder(self, queryable_or_builder):
        if isinstance(queryable_or_builder, Q):
            return self.parse_builder(queryable_or_builder)
        else:
            return self.create_expression_from_query(queryable_or_builder)

    def parse_builder(self, builder):
        for branch in builder.iter_branches():
            self.parse_query_branch(branch)
        return self.create_expression_from_query(builder.queryable)

    def parse_query_branch(self, query):
        alias = self.get_or_create_query_alias(query)
        return alias

    def get_or_create_query_alias(self, query):
        alias = self.get_query_alias(query)
        if alias is None:
            alias = self.create_query_alias(query)
        return alias

    def get_query_alias(self, query):
        query_id = id(query)
        return self.query_alias_map.get(query_id)

    def create_query_alias(self, query):
        expression = self.create_expression_from_query(query)
        alias = Alias(self.cte.append(expression))
        query_id = id(query)
        self.query_alias_map[query_id] = alias
        return alias

    def create_expression_from_query(self, query):
        if isinstance(query, query_module.Select):
            expr = self.create_select(query)
        # TODO: Update must come before Insert, as it's
        # inherited. Probably need a better way of deciding which is
        # which. Perhaps a visitor pattern?
        elif isinstance(query, query_module.Update):
            expr = self.create_update(query)
        elif isinstance(query, query_module.Insert):
            expr = self.create_insert(query)
        elif isinstance(query, query_module.Delete):
            expr = self.create_delete(query)
        else:
            raise TypeError(f'Unknown query: {query}')
        return expr

    def create_select(self, query):
        return self.select_strategy.parse_query(query)

    def create_insert(self, query):
        return self.insert_strategy.parse_query(query)

    def create_update(self, query):
        return self.update_strategy.parse_query(query)

    def create_delete(self, query):
        return self.delete_strategy.parse_query(query)

    def parse_chained_relation(self, relation):
        if isinstance(relation, query_module.Insert):
            return self.get_or_create_query_alias(relation)
        else:
            return relation
