from functools import partial

from polecat.db.query import query as query_module
from psycopg2.sql import SQL, Placeholder

from .expression import Expression


class Values(Expression):
    def __init__(self, values, relation=None):
        self.values = values
        self.relation = relation
        self.keyword = 'VALUES'

    def to_sql(self):
        if isinstance(self.values, query_module.Values):
            get_values_sql = partial(
                self.get_values_sql_from_values, self.values
            )
        else:
            get_values_sql = partial(
                self.get_values_sql_from_dict, self.values
            )
        return self.get_values_sql(get_values_sql)

    def get_values_sql(self, get_values_sql):
        values_sql, values_args = get_values_sql()
        joined_sql = SQL(', ').join(
            SQL('({})').format(
                SQL(', ').join(row_sql)
            )
            for row_sql in values_sql
        )
        return SQL('%s {}' % self.keyword).format(joined_sql), values_args

    def get_values_sql_from_values(self, values):
        column_values_sql = []
        column_values = ()
        for row in values.iter_rows():
            row_values_sql = []
            for column_name, column_value in row:
                value_sql, value = self.value_to_sql(column_value, column_name)
                row_values_sql.append(value_sql)
                column_values += value
            column_values_sql.append(row_values_sql)
        return column_values_sql, column_values

    def get_values_sql_from_dict(self, values_dict):
        column_values_sql = []
        column_values = ()
        for column_name, column_value in values_dict.items():
            value_sql, value = self.value_to_sql(column_value, column_name)
            column_values_sql.append(value_sql)
            column_values += value
        return (column_values_sql,), column_values

    def value_to_sql(self, value, column_name=None):
        if isinstance(value, Expression):
            sql, args = value.to_sql()
            return SQL('{}').format(sql), args
        else:
            if self.relation and column_name:
                column = self.relation.get_column(column_name)
                value = column.to_db_value(value)
            return Placeholder(), (value,)

    def iter_column_names(self):
        if isinstance(self.values, dict):
            return self.values.keys()
        else:
            return self.values.iter_column_names()
