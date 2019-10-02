from polecat.utils import to_tuple
from psycopg2.sql import SQL, Identifier

from ..query.selection import Selection
from ..schema import ReverseColumn
from .expression.alias import Alias
from .expression.array_agg import ArrayAgg
from .expression.as_ import As
from .expression.join import Join, LateralJoin
from .expression.raw import RawSQL
from .expression.select import Select
from .expression.subquery import Subquery
from .expression.where import Where


class SelectStrategy:
    def __init__(self, root_strategy):
        self.root = root_strategy
        self.relation_counter = 0
        self.lateral_counter = 0
        self.agg_counter = 0

    def parse_query(self, queryable):
        expr = self.parse_query_from_components(
            queryable.source,
            queryable.selection,
            queryable=queryable
        )
        if queryable.recurse_column:
            alias = self.root.create_alias(expr)
            top_level = Select(
                alias,
                columns=expr.columns + tuple(expr.subqueries.keys())
            )
            alias.push_selection(Selection(queryable.recurse_column))
            cte_as = alias.expression
            join = Join(alias)
            recursive_expr = self.parse_query_from_components(
                queryable.source,
                queryable.selection,
                queryable=queryable
            )
            recursive_expr.push_selection(Selection(queryable.recurse_column))
            # TODO: This is the worst.
            if isinstance(recursive_expr.relation, As):
                expr_to_update = recursive_expr.relation.expression.expression
            else:
                expr_to_update = recursive_expr
            expr_to_update.joins = to_tuple(expr_to_update.joins) + (join,)
            expr_to_update.where = Where(
                id=SQL('{}.{}').format(
                    Identifier(alias.alias),
                    Identifier(queryable.recurse_column)
                )
            )
            cte_as.set_recursive_expression(recursive_expr)
            expr = top_level
        return expr

    def parse_query_from_components(self, relation, selection, queryable=None):
        relation = self.parse_relation(relation)
        if selection.has_lookups():
            relation = self.create_alias_for_relation(relation)
        columns = selection.fields
        subqueries, joins = self.create_subqueries(relation, selection)
        return Select(
            relation, columns, subqueries, joins,
            limit=queryable.limit if queryable else None,
            order=queryable.order if queryable else None
        )

    def parse_relation(self, relation):
        return self.root.parse_chained_relation(relation)

    def create_alias_for_relation(self, relation):
        # TODO: Using the factory here when we've already got an "As"
        # spuriously increments the relation counter.
        alias = As.factory(relation, f't{self.relation_counter}')
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
                # TODO: This is ugly as. The problem is that
                # subqueries aren't necessarily columns, they can be
                # just named subqueries. Need to separate them.
                try:
                    column = relation.get_column(name)
                    if isinstance(column, ReverseColumn):
                        alias_column = 'array_agg'
                    else:
                        alias_column = None
                except KeyError:
                    alias_column = None
                subqueries[name] = Alias(expr.alias, column=alias_column)
            else:
                expr = self.create_detached_subquery(subquery)
                subqueries[name] = expr
        return subqueries, joins

    def create_lateral_subquery(self, relation, selection, column_name):
        subrelation = relation.get_subrelation(column_name)
        subquery = self.parse_query_from_components(subrelation, selection)
        self.add_where_clause_to_lateral_subquery(relation, column_name, subquery)
        subquery = self.add_aggregation_to_lateral_subquery(relation, column_name, subquery)
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

    def add_where_clause_to_lateral_subquery(self, relation, column_name, subquery):
        column = relation.get_column(column_name)
        if isinstance(column, ReverseColumn):
            subquery.where = Where(**{
                column.related_column.name: SQL('{}.id').format(
                    Identifier(relation.alias)
                )
            })
        else:
            subquery.where = Where(**{
                'id': SQL('{}.{}').format(
                    Identifier(relation.alias),
                    Identifier(column_name)
                )
            })

    def add_aggregation_to_lateral_subquery(self, relation, column_name, subquery):
        column = relation.get_column(column_name)
        if isinstance(column, ReverseColumn):
            agg_alias = self.create_alias_name_for_aggregate()
            subquery = Select(
                As(Subquery(subquery), agg_alias),
                columns=ArrayAgg(Alias(agg_alias))
            )
        return subquery

    def create_lateral_condition(self, relation, lateral_alias, column_name):
        # TODO: Replace this with something other than a raw sql string.
        column = relation.get_column(column_name)
        if isinstance(column, ReverseColumn):
            return RawSQL(SQL('TRUE'))
        else:
            return RawSQL(SQL('TRUE'))

    def create_detached_subquery(self, subquery):
        return Subquery(self.root.parse_queryable_or_builder(subquery))

    def create_alias_name_for_lateral(self):
        alias_name = f'j{self.lateral_counter}'
        self.lateral_counter += 1
        return alias_name

    def create_alias_name_for_aggregate(self):
        alias_name = f'a{self.agg_counter}'
        self.agg_counter += 1
        return alias_name
