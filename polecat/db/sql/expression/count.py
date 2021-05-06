from psycopg2.sql import SQL

from .expression import Expression


class Count(Expression):
    def __init__(self, expression=None):
        self.expression = expression

    def to_sql(self):
        return SQL('COUNT(*)'), ()
