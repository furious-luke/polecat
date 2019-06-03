from psycopg2.sql import SQL, Identifier

from .expression import Expression
from .insert import Insert


class Update(Insert):
    def to_sql(self):
        if isinstance(self.values, Expression):
            prefix_sql = SQL('')
            suffix_sql = SQL('')
            get_values_func = self.get_values_sql_from_expression
        else:
            prefix_sql = SQL('(')
            suffix_sql = SQL(')')
            get_values_func = self.get_values_sql_from_dict
        column_names_sql, column_values_sql, column_values = get_values_func()
        returning_sql = map(Identifier, self.returning)
        sql = SQL('UPDATE {} SET ({}) = {}{}{} RETURNING {}').format(
            Identifier(self.relation.name),
            SQL(', ').join(column_names_sql),
            prefix_sql,
            SQL(', ').join(column_values_sql),
            suffix_sql,
            SQL(', ').join(returning_sql)
        )
        return sql, tuple(column_values)
