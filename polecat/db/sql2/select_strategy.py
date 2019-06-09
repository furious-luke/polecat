from psycopg2.sql import SQL, Identifier

from ..query.selection import Selection
from ..schema import ReverseColumn
from .expression.alias import Alias
from .expression.as_ import As
from .expression.join import LateralJoin
from .expression.raw import RawSQL
from .expression.select import Select
from .expression.subquery import Subquery


class SelectStrategy:
    def __init__(self, root_strategy):
        self.root = root_strategy
        self.relation_counter = 0
        self.lateral_counter = 0

    def parse_query(self, queryable):
        return self.parse_query_from_components(
            queryable.source,
            queryable.selection
        )

    def parse_query_from_components(self, relation, selection):
        self.add_select_columns_to_root(selection)
        relation = self.parse_relation(relation)
        if selection.has_lookups():
            relation = self.create_alias_for_relation(relation)
        columns = selection.fields
        subqueries, joins = self.create_subqueries(relation, selection)
        return Select(relation, columns, subqueries, joins)

    def add_select_columns_to_root(self, selection):
        self.root.add_select_columns(selection.all_fields())

    def parse_relation(self, relation):
        return self.root.parse_chained_relation(relation)

    def create_alias_for_relation(self, relation):
        alias = As(relation, f't{self.relation_counter}')
        self.relation_counter += 1
        return alias

    def create_subqueries(self, relation, selection):
        lookups = selection.lookups
        subqueries = {}
        joins = []
        for name, subquery in lookups.items():
            if isinstance(subquery, Selection):
                expr = self.create_lateral_subquery(relation, subquery, name)
                joins.append(expr)
                subqueries[name] = Alias(expr.alias)
            else:
                expr = self.create_detached_subquery(subquery)
                subqueries[name] = expr
        return subqueries, joins

    def create_lateral_subquery(self, relation, selection, column_name):
        subrelation = relation.get_subrelation(column_name)
        subquery = self.parse_query_from_components(subrelation, selection)
        lateral_alias = self.create_alias_name_for_lateral()
        return LateralJoin(
            subquery,
            join_type=LateralJoin.LEFT,
            alias=lateral_alias,
            condition=self.create_lateral_condition(
                relation,
                lateral_alias,
                column_name
            )
        )

    def create_lateral_condition(self, relation, lateral_alias, column_name):
        # TODO: Replace this with something other than a raw sql string.
        column = relation.get_column(column_name)
        if isinstance(column, ReverseColumn):
            return RawSQL(
                SQL('{}.id = {}.{}').format(
                    Identifier(relation.alias),
                    Identifier(lateral_alias),
                    Identifier(column.related_column.name)
                )
            )
        else:
            return RawSQL(
                SQL('{}.id = {}.{}').format(
                    Identifier(lateral_alias),
                    Identifier(relation.alias),
                    Identifier(column_name)
                )
            )

    def create_detached_subquery(self, subquery):
        return Subquery(self.root.parse_queryable_or_builder(subquery))

    def create_alias_name_for_lateral(self):
        alias_name = f'j{self.lateral_counter}'
        self.lateral_counter += 1
        return alias_name
