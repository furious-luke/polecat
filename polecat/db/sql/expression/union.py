from psycopg2.sql import SQL

from .expression import Expression


class Union(Expression):
    def __init__(self, expressions=None):
        self.expressions = expressions or []

    def add_expression(self, expression):
        self.expressions.append(expression)

    def to_sql(self):
        all_sql = []
        all_args = ()
        for expr in self.expressions:
            sql, args = expr.to_sql()
            all_sql.append(sql)
            all_args += args
        return SQL(' UNION ALL ').join(all_sql), all_args

    def push_selection(self, selection):
        for expr in self.expressions:
            expr.push_selection(selection)
