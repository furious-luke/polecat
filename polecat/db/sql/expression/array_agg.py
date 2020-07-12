from psycopg2.sql import SQL

from .expression import Expression


class ArrayAgg(Expression):
    def __init__(self, term):
        super().__init__(term)
        self.expression = self.term  # TODO: Deprecate

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        return (
            SQL('array_agg({})').format(expr_sql),
            expr_args
        )
