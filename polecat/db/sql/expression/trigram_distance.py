from psycopg2.sql import SQL, Identifier

from .expression import Expression


class TrigramDistance(Expression):
    def __init__(self, column, term):
        self.column = column
        self.term = term

    def to_sql(self):
        return SQL('{} <-> %s').format(
            Identifier(self.column)
        ), (self.term,)
