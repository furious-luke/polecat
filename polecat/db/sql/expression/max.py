from psycopg2.sql import SQL, Identifier

from .expression import Expression


class Max(Expression):
    def __init__(self, expression):
        self.expression = expression

    def to_sql(self):
        if not isinstance(self.expression, str):
            sql, args = self.expression.to_sql()
        else:
            sql, args = Identifier(self.expression), ()
        return SQL('MAX({})').format(sql), args
