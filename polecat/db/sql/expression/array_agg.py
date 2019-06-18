from psycopg2.sql import SQL

from .expression import Expression


class ArrayAgg(Expression):
    def __init__(self, expression):
        self.expression = expression

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        return (
            SQL('array_agg({})').format(expr_sql),
            expr_args
        )
