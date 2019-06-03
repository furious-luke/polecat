from psycopg2.sql import SQL, Identifier

from .expression import Expression


class Alias(Expression):
    def __init__(self, expression):
        self.expression = expression

    @property
    def alias(self):
        return self.expression.alias

    def to_sql(self):
        try:
            alias = self.expression.alias
        except AttributeError:
            alias = self.expression
        return (
            SQL('{}').format(
                Identifier(alias)
            ),
            ()
        )

    def get_subrelation(self, name):
        # TODO: This feels like bad design. Not sure how to correct
        # just at the moment, and at least it's clear what it's doing.
        return self.expression.get_subrelation(name)
