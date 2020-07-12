from psycopg2.sql import SQL, Identifier

from .expression import Expression


class As(Expression):
    @classmethod
    def factory(cls, expression, alias):
        if not isinstance(expression, As):
            return cls(expression, alias)
        else:
            return expression

    def __init__(self, term, alias):
        super().__init__(term)
        self.expression = self.term  # TODO: Deprecate
        self.alias = alias

    # TODO: Deprecate
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
