from itertools import chain

from psycopg2.sql import SQL, Identifier

from .expression import Expression


class Select(Expression):
    def __init__(self, relation, columns, subqueries=None, joins=None):
        self.relation = relation
        self.columns = columns or ()
        self.subqueries = subqueries or {}
        self.joins = joins or ()

    def to_sql(self):
        columns_sql = self.get_columns_sql()
        all_subquery_sql, all_subquery_args = self.get_subquery_sql()
        rel_sql, rel_args = self.relation.to_sql()
        joins_sql, joins_args = self.get_all_joins_sql()
        sql = SQL('SELECT {} FROM {}{}').format(
            SQL(', ').join(chain(columns_sql, all_subquery_sql)),
            rel_sql,
            joins_sql
        )
        return sql, all_subquery_args + rel_args + joins_args

    def get_subquery_sql(self):
        all_subquery_sql = []
        all_subquery_args = []
        for as_name, subquery in self.subqueries.items():
            subquery_sql, subquery_args = subquery.to_sql()
            sql = SQL('{} AS {}').format(
                subquery_sql,
                Identifier(as_name)
            )
            all_subquery_sql.append(sql)
            all_subquery_args.append(subquery_args)
        return all_subquery_sql, tuple(all_subquery_args)

    def get_columns_sql(self):
        columns_sql = []
        for name in self.columns:
            name_ident = Identifier(name)
            sql = SQL('{}.{} AS {}').format(
                Identifier(self.relation.alias),
                name_ident,
                name_ident
            )
            columns_sql.append(sql)
        return columns_sql

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

    def iter_column_names(self):
        for name in self.columns:
            yield name
        for name in self.subqueries.keys():
            yield name
