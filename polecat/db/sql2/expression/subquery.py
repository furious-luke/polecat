from psycopg2.sql import SQL

from .expression import Expression


class Subquery(Expression):
    def __init__(self, expression):
        self.expression = expression

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        return (
            SQL('({})').format(expr_sql),
            expr_args
        )

    def get_subrelation(self, name):
        # TODO: This feels like bad design. Not sure how to correct
        # just at the moment, and at least it's clear what it's doing.
        return self.expression.get_subrelation(name)

    def iter_column_names(self):
        # TODO: This feels like bad design. Not sure how to correct
        # just at the moment, and at least it's clear what it's doing.
        return iter(self.expression.iter_column_names())
