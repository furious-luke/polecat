from psycopg2.sql import SQL

from .expression import Expression


class Subquery(Expression):
    def __init__(self, expression):
        self.expression = expression

    @property
    def alias(self):
        return self.expression.alias

    @property
    def root_relation(self):
        return self.expression.root_relation

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        return (
            SQL('({})').format(expr_sql),
            expr_args
        )

    def get_subrelation(self, name):
        # TODO: This feels like bad design. Not sure how to correct
        # just at the moment, and at least it's clear what it's doing.
        return self.expression.get_subrelation(name)

    def iter_column_names(self):
        # TODO: This feels like bad design. Not sure how to correct
        # just at the moment, and at least it's clear what it's doing.
        return iter(self.expression.iter_column_names())

    def get_column(self, name):
        # TODO: Also bad design, but also what's the difference
        # between this and the above? Looks like the above just does
        # 'this.related_table'.
        return self.expression.get_column(name)

    def push_selection(self, selection=None):
        self.expression.push_selection(selection)
