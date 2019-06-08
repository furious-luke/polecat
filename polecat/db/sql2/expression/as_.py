from psycopg2.sql import SQL, Identifier

from .expression import Expression


class As(Expression):
    def __init__(self, expression, alias):
        self.expression = expression
        self.alias = alias

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        return (
            self.get_as_sql(expr_sql),
            expr_args
        )

    def get_as_sql(self, expression_sql):
        return SQL('{} AS {}').format(
            expression_sql,
            Identifier(self.alias)
        )

    def get_subrelation(self, name):
        # TODO: This feels like bad design. Not sure how to correct
        # just at the moment, and at least it's clear what it's doing.
        return self.expression.get_subrelation(name)