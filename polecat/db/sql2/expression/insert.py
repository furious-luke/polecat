from psycopg2.sql import SQL, Identifier

from .expression import Expression
from .value import value_to_sql


class Insert(Expression):
    def __init__(self, relation, values, returning=None):
        self.relation = relation
        self.values = values
        self.returning = returning or ()
        if 'id' not in self.returning:
            self.returning += ('id',)

    def to_sql(self):
        column_names_sql, column_values_sql, column_values = self.get_values_sql()
        returning_sql = map(Identifier, self.returning)
        sql = SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING {}').format(
            Identifier(self.relation.name),
            SQL(', ').join(column_names_sql),
            SQL(', ').join(column_values_sql),
            SQL(', ').join(returning_sql)
        )
        return sql, tuple(column_values)

    def get_values_sql(self):
        column_names_sql = []
        column_values_sql = []
        column_values = []
        for column_name, column_value in self.values.items():
            column = self.relation.get_column(column_name)
            column_names_sql.append(Identifier(column_name))
            value_sql, value = value_to_sql(column, column_value)
            column_values_sql.append(value_sql)
            column_values.extend(value)
        return column_names_sql, column_values_sql, column_values
