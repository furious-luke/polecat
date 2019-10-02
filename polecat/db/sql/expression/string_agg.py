from psycopg2.sql import SQL, Identifier

from .expression import Expression


class StringAgg(Expression):
    def __init__(self, expression, separator=' '):
        self.expression = expression
        self.separator = separator

    @property
    def alias(self):
        return self.expression.alias

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        return (
            SQL('string_agg({}, {})').format(
                expr_sql, Identifier(self.separator)
            ),
            expr_args
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

    def has_column(self, name):
        # TODO: Also bad design, but also what's the difference
        # between this and the above? Looks like the above just does
        # 'this.related_table'.
        return self.expression.has_column(name)

    def push_selection(self, selection=None):
        self.expression.push_selection(selection)
