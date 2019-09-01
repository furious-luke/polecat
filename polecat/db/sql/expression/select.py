from itertools import chain

from polecat.utils import to_tuple
from psycopg2.sql import SQL, Identifier

from .expression import Expression


class Select(Expression):
    def __init__(self, relation, columns=None, subqueries=None, joins=None,
                 where=None, limit=None, order=None):
        self.relation = relation
        self.columns = columns or ()
        self.subqueries = subqueries or {}
        self.joins = joins or ()
        self.where = where
        self.limit = limit
        self.order = to_tuple(order)

    @property
    def root_relation(self):
        return self.relation.root_relation

    def to_sql(self):
        columns_sql, columns_args = self.get_columns_sql()
        all_subquery_sql, all_subquery_args = self.get_subquery_sql()
        rel_sql, rel_args = self.relation.to_sql()
        joins_sql, joins_args = self.get_all_joins_sql()
        where_sql, where_args = self.get_where_sql()
        limit_sql = self.get_limit_sql()
        order_sql = self.get_order_sql()
        sql = SQL('SELECT {} FROM {}{}{}{}{}').format(
            SQL(', ').join(chain(columns_sql, all_subquery_sql)),
            rel_sql,
            joins_sql,
            where_sql,
            order_sql,
            limit_sql
        )
        return sql, columns_args + all_subquery_args + rel_args + joins_args + where_args

    def get_subquery_sql(self):
        all_subquery_sql = []
        all_subquery_args = ()
        for as_name, subquery in self.subqueries.items():
            subquery_sql, subquery_args = subquery.to_sql()
            sql = SQL('{} AS {}').format(
                subquery_sql,
                Identifier(as_name)
            )
            all_subquery_sql.append(sql)
            all_subquery_args += subquery_args
        return all_subquery_sql, all_subquery_args

    def get_columns_sql(self):
        columns_sql = []
        columns_args = ()
        for name in to_tuple(self.columns):
            if isinstance(name, Expression):
                sql, args = name.to_sql()
            elif isinstance(name, SQL):
                sql = name
                args = ()
            else:
                name_ident = Identifier(name)
                sql = SQL('{}.{} AS {}').format(
                    Identifier(self.relation.alias),
                    name_ident,
                    name_ident
                )
                args = ()
            columns_sql.append(sql)
            columns_args += args
        if not columns_sql and not self.subqueries:
            columns_sql = [SQL('*')]
        return columns_sql, columns_args

    def get_all_joins_sql(self):
        joins_sql = []
        joins_args = ()
        for join in self.joins:
            sql, args = self.get_join_sql(join)
            joins_sql.append(sql)
            joins_args += args
        if len(joins_sql):
            joins_sql = SQL(' ').join(joins_sql)
            return SQL(' {}').format(joins_sql), joins_args
        else:
            return SQL(''), ()

    def get_join_sql(self, join):
        return join.to_sql()

    def get_where_sql(self):
        if self.where:
            sql, args = self.where.get_sql(self.relation)
            return SQL(' WHERE {}').format(sql), args
        else:
            return SQL(''), ()

    def get_limit_sql(self):
        if self.limit is not None:
            # TODO: Is this risky?
            return SQL(f' LIMIT {int(self.limit)}')
        else:
            return SQL('')

    def get_order_sql(self):
        if self.order:
            columns = ', '.join(self.parse_order_column(o) for o in self.order)
            return SQL(f' ORDER BY {columns}')
        else:
            return SQL('')

    def parse_order_column(self, column):
        if column[0] == '-':
            return f'{column[1:]} DESC'
        else:
            return column

    def iter_column_names(self):
        for name in self.columns:
            yield name
        for name in self.subqueries.keys():
            yield name

    def get_column(self, name):
        # TODO: Not sure a select should be running "get_column".
        return self.relation.get_column(name)

    def get_subrelation(self, name):
        return self.relation.get_subrelation(name)

    def push_selection(self, selection=None):
        from ...schema import ReverseColumn
        # TODO: Efficiency. Everything.
        for column_name in selection or ():
            if column_name not in self.columns and column_name not in self.subqueries:
                self.columns += (column_name,)
        # TODO: Forgot that columns can be a subquery. I'll need to
        # allow subqueries to return a list columns they require. For
        # now, skip it.
        to_push = self.columns if isinstance(self.columns, (tuple, list)) else ()
        for column_name in self.subqueries.keys():
            try:
                column = self.relation.get_column(column_name)
            except KeyError:
                continue
            if not isinstance(column, ReverseColumn):
                to_push += (column_name,)
        if self.where:
            to_push += self.where.get_primary_columns()
        self.relation.push_selection(to_push)
        for join in self.joins:
            join.push_selection()
