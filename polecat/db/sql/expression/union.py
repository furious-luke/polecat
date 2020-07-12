from psycopg2.sql import SQL

from .expression import Expression


class Union(Expression):
    def __init__(self, expressions=None):
        super().__init__(expressions[0] if expressions else None)
        self.expressions = expressions or []

    def add_expression(self, expression):
        self.expressions.append(expression)
        if not self.term:
            self.term = expression

    def to_sql(self):
        all_sql = []
        all_args = ()
        for expr in self.expressions:
            sql, args = expr.to_sql()
            all_sql.append(sql)
            all_args += args
        return SQL(' UNION ALL ').join(all_sql), all_args

    def get_subrelation(self, name):
        return self.expressions[-1].get_subrelation(name)

    def push_selection(self, selection):
        for expr in self.expressions:
            expr.push_selection(selection)
