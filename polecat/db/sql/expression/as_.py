from psycopg2.sql import SQL, Identifier

from .expression import Expression


class As(Expression):
    @classmethod
    def factory(cls, expression, alias):
        if not isinstance(expression, As):
            return cls(expression, alias)
        else:
            return expression

    def __init__(self, expression, alias):
        self.expression = expression
        self.alias = alias

    @property
    def root_relation(self):
        return self.expression.root_relation

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        as_sql, as_args = self.get_as_sql(expr_sql)
        return (
            as_sql,
            expr_args + as_args
        )

    def get_as_sql(self, expression_sql):
        return SQL('{} AS {}').format(
            expression_sql,
            Identifier(self.alias)
        ), ()

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
