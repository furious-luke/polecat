from psycopg2.sql import SQL

from .expression import Expression


class JSON(Expression):
    def __init__(self, expression):
        self.expression = expression

    def to_sql(self):
        sql, args = self.expression.to_sql()
        return SQL('SELECT row_to_json(__tl) FROM {} AS __tl').format(
            sql
        ), args

    def push_selection(self, selection=None):
        self.expression.push_selection(selection)
