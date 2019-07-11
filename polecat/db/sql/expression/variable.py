from psycopg2.sql import SQL, Identifier

from .expression import Expression


class LocalVariable(Expression):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def to_sql(self):
        return (
            SQL('SET LOCAL {} TO %s').format(
                Identifier(self.key)
            ),
            (self.value,)
        )


class LocalRole(Expression):
    def __init__(self, role):
        self.role = role

    def to_sql(self):
        return (
            SQL('SET LOCAL ROLE {}').format(
                Identifier(self.role)
            ),
            ()
        )
