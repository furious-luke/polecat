from psycopg2.sql import SQL, Identifier

from .expression import Expression
from .insert import Insert


class Update(Insert):
    def __init__(self, *args, where=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.where = where

    @property
    def alias(self):
        return self.relation.alias

    def to_sql(self):
        if isinstance(self.values, Expression):
            prefix_sql = SQL('')
            suffix_sql = SQL('')
            # TODO: This is ugly as.
            self.values.keyword = 'ROW'
            get_values_func = self.get_values_sql_from_expression
        else:
            prefix_sql = SQL('ROW (')
            suffix_sql = SQL(')')
            get_values_func = self.get_values_sql_from_dict
        column_names_sql, column_values_sql, column_values = get_values_func()
        returning_sql = map(Identifier, self.returning)
        where_sql, where_args = self.get_where_sql()
        sql = SQL('UPDATE {} SET ({}) = {}{}{}{} RETURNING {}').format(
            Identifier(self.relation.alias),
            SQL(', ').join(column_names_sql),
            prefix_sql,
            SQL(', ').join(column_values_sql),
            suffix_sql,
            where_sql,
            SQL(', ').join(returning_sql)
        )
        return sql, tuple(column_values) + where_args

    def get_where_sql(self):
        if self.where:
            sql, args = self.where.get_sql(self.relation)
            return SQL(' WHERE {}').format(sql), args
        else:
            return SQL(''), ()
