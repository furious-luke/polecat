from psycopg2.sql import SQL


class Not:
    def __init__(self, expression):
        self.expression = expression

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        return SQL('NOT {}').format(expr_sql), expr_args
