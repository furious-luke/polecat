from psycopg2.sql import Identifier

from ..sql_term import SqlTerm


class Relation(SqlTerm):
    def __init__(self, name):
        self.name = name

    # TODO: Deprecate.
    @property
    def alias(self):
        return self.name

    def get_alias(self):
        return self.name

    def to_sql(self):
        return Identifier(self.name), ()
