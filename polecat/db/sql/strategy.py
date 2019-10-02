from psycopg2.sql import SQL, Identifier

from ..query import Q
from ..query import query as query_module
from ..schema.role import Role
from .delete_strategy import DeleteStrategy
from .expression.alias import Alias
from .expression.as_ import As
from .expression.cte import CTE
from .expression.expression import Expression
from .expression.json import JSON
from .expression.multi import Multi
from .expression.raw import RawSQL
from .expression.select import Select
from .expression.string_agg import StringAgg
from .expression.subquery import Subquery
from .expression.union import Union
from .expression.variable import LocalRole, LocalVariable
from .expression.where import Where
from .insert_if_missing_strategy import InsertIfMissingStrategy
from .insert_strategy import InsertStrategy
from .select_strategy import SelectStrategy
from .update_strategy import UpdateStrategy


class Strategy:
    def __init__(self):
        self.select_strategy = SelectStrategy(self)
        self.insert_strategy = InsertStrategy(self)
        self.insert_if_missing_strategy = InsertIfMissingStrategy(self)
        self.update_strategy = UpdateStrategy(self)
        self.delete_strategy = DeleteStrategy(self)

    def parse(self, queryable_or_builder):
        self.cte = CTE()
        self.query_alias_map = {}
        self.chained_relation_counter = 0
        expr = self.parse_queryable_or_builder(queryable_or_builder)
        expr = self.wrap_final_expression(expr)
        self.cte.set_final_expression(expr)
        self.push_selection_to_relations()
        return self.wrap_with_session(queryable_or_builder)

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
        alias = self.create_alias(expression)
        query_id = id(query)
        self.query_alias_map[query_id] = alias
        return alias

    def create_alias(self, expression):
        return Alias(self.cte.append(expression))

    def create_expression_from_query(self, query):
        alias = self.get_query_alias(query)
        if alias is not None:
            return alias
        if isinstance(query, query_module.Select):
            expr = self.create_select(query)
            # TODO: Update must come before Insert, as it's
            # inherited. Probably need a better way of deciding which is
            # which. Perhaps a visitor pattern?
        elif isinstance(query, query_module.Update):
            expr = self.create_update(query)
        elif isinstance(query, query_module.InsertIfMissing):
            expr = self.create_insert_if_missing(query)
        elif isinstance(query, query_module.Insert):
            expr = self.create_insert(query)
        elif isinstance(query, query_module.Delete):
            expr = self.create_delete(query)
        elif isinstance(query, query_module.Filter):
            expr = self.create_filter(query)
        elif isinstance(query, query_module.Join):
            expr = self.create_join(query)
        elif isinstance(query, query_module.Common):
            expr = self.create_common(query)
        elif isinstance(query, Expression):
            expr = query
        else:
            raise TypeError(f'Unknown query: {query}')
        return expr

    def create_select(self, query):
        return self.select_strategy.parse_query(query)

    def create_insert(self, query):
        return self.insert_strategy.parse_query(query)

    def create_insert_if_missing(self, query):
        return self.insert_if_missing_strategy.parse_query(query)

    def create_update(self, query):
        return self.update_strategy.parse_query(query)

    def create_delete(self, query):
        return self.delete_strategy.parse_query(query)

    def create_filter(self, query):
        # TODO: Should maybe factor this out into a filter
        # strategy?
        return Select(
            self.parse_chained_relation(query.source),
            where=Where(
                **query.options
            )
        )

    def create_join(self, query):
        # TODO: Currently assumes parent is a select?
        rel = self.parse_chained_relation(query.source)
        select = rel.expression.expression
        column_name = select.columns[0]
        return Select(
            rel,
            As(
                StringAgg(
                    RawSQL(
                        SQL('{}.{}').format(
                            Identifier(rel.alias),
                            Identifier(column_name)
                        )
                    ),
                    separator=query.separator
                ),
                column_name
            )
        )

    def create_common(self, query):
        for subquery in query.subqueries[:-1]:
            expr = self.parse_queryable_or_builder(subquery)
            self.cte.append(expr)
        return self.parse_queryable_or_builder(query.subqueries[-1])

    def parse_chained_relation(self, relation):
        # TODO: I'm not too happy about the type conditional here.
        if isinstance(relation, (query_module.Insert, query_module.Update)):
            return self.get_or_create_query_alias(relation)
        elif isinstance(relation, query_module.Filter):
            counter = self.chained_relation_counter
            self.chained_relation_counter += 1
            return As(
                Subquery(
                    self.create_filter(relation)
                ),
                f'r{counter}'
            )
        elif isinstance(relation, query_module.Select):
            counter = self.chained_relation_counter
            self.chained_relation_counter += 1
            return As(
                Subquery(
                    self.create_select(relation)
                ),
                f'r{counter}'
            )
        else:
            return relation

    def wrap_final_expression(self, expression):
        if isinstance(expression, Select):
            expression = JSON(Subquery(expression))
        elif isinstance(expression, Alias):
            expression = JSON(expression)
        elif isinstance(expression, Union) or expression.returning:
            expression = JSON(Subquery(Select(Alias(self.cte.append(expression)))))
        return expression

    def push_selection_to_relations(self):
        for expr in self.cte.iter_expressions():
            expr.push_selection()

    def wrap_with_session(self, builder):
        session = getattr(builder, 'session', None)
        if not session or session.is_empty():
            return self.cte
        local_expressions = []
        if session.role:
            # TODO: Need to type this.
            assert isinstance(session.role, Role)
            local_expressions.append(LocalRole(session.role.dbname))
        for key, value in session.variables.items():
            local_expressions.append(LocalVariable(key, value))
        local_expressions.append(self.cte)
        return Multi(*local_expressions)
