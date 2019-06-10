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

    def get_column(self, name):
        # TODO: Also bad design, but also what's the difference
        # between this and the above? Looks like the above just does
        # 'this.related_table'.
        return self.expression.get_column(name)

    def push_selection(self, selection=None):
        self.expression.push_selection(selection)
