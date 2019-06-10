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

    @property
    def alias(self):
        return self.relation.alias

    def to_sql(self):
        # TODO: Generating SQL for inserts could be improved by using
        # a Values expression instead of this mishmash.
        if isinstance(self.values, Expression):
            prefix_sql = SQL('')
            suffix_sql = SQL('')
            get_values_func = self.get_values_sql_from_expression
        else:
            prefix_sql = SQL('VALUES (')
            suffix_sql = SQL(')')
            get_values_func = self.get_values_sql_from_dict
        column_names_sql, column_values_sql, column_values = get_values_func()
        returning_sql = map(Identifier, self.returning)
        sql = SQL('INSERT INTO {} ({}) {}{}{} RETURNING {}').format(
            Identifier(self.relation.name),
            SQL(', ').join(column_names_sql),
            prefix_sql,
            SQL(', ').join(column_values_sql),
            suffix_sql,
            SQL(', ').join(returning_sql)
        )
        return sql, tuple(column_values)

    def get_values_sql_from_expression(self):
        column_names_sql = []
        for column_name in self.values.iter_column_names():
            column_names_sql.append(Identifier(column_name))
        column_values_sql, column_values = self.values.to_sql()
        return column_names_sql, [column_values_sql], column_values

    def get_values_sql_from_dict(self):
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

    def get_subrelation(self, name):
        # TODO: This feels like bad design. Not sure how to correct
        # just at the moment, and at least it's clear what it's doing.
        return self.relation.get_subrelation(name)

    def get_column(self, name):
        # TODO: Also bad design, but also what's the difference
        # between this and the above? Looks like the above just does
        # 'this.related_table'.
        # TODO: This should be filtered by "returning".
        return self.relation.get_column(name)
