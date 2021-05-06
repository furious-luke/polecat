from psycopg2.sql import SQL, Identifier

from .expression import Expression


class Correlation(Expression):
    def __init__(self, parent_relation, column_name):
        self.parent_relation = parent_relation
        self.column_name = column_name

    def to_sql(self):
        return SQL('{}.{}').format(
            Identifier(self.parent_relation.alias),
            Identifier(self.column_name),
        ), ()

    def _find_subquery(self):
        pass
