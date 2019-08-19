from psycopg2.sql import SQL, Identifier

from .as_ import As
from .expression import Expression


class CTE(Expression):
    def __init__(self):
        self.expression = None
        self.common_expressions = []
        self.alias_counter = 0

    def append(self, expression):
        alias = self.create_alias(expression)
        self.common_expressions.append(alias)
        return alias

    def prepend(self, expression):
        alias = self.create_alias(expression)
        self.expressions.insert(0, expression)
        return alias

    def set_final_expression(self, expression):
        self.expression = expression

    def create_alias(self, expression):
        alias = CTEAs(expression, f'c{self.alias_counter}')
        self.alias_counter += 1
        return alias

    def to_sql(self):
        if self.common_expressions:
            return self.to_cte_sql()
        else:
            return self.expression.to_sql()

    def to_cte_sql(self):
        common_sql, common_args = self.get_common_sql()
        final_sql, final_args = self.expression.to_sql()
        return (
            SQL('WITH {} {}').format(
                SQL(', ').join(common_sql),
                final_sql
            ),
            common_args + final_args
        )

    def get_common_sql(self):
        common_sql = []
        common_args = ()
        for expr in self.common_expressions:
            sql, args = expr.to_sql()
            common_sql.append(sql)
            common_args += args
        return common_sql, common_args

    def iter_expressions(self):
        for expr in self.common_expressions:
            yield expr
        yield self.expression


class CTEAs(As):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recursive_expression = None

    def get_as_sql(self, expression_sql):
        rec_sql, rec_args = self.get_recursive_sql()
        return SQL('{}{} AS ({}{})').format(
            SQL('RECURSIVE ' if self.recursive_expression else ''),
            Identifier(self.alias),
            expression_sql,
            rec_sql
        ), rec_args

    def get_recursive_sql(self):
        if self.recursive_expression:
            expr_sql, expr_args = self.recursive_expression.to_sql()
            return SQL(' UNION ALL {}').format(
                expr_sql
            ), expr_args
        else:
            return SQL(''), ()

    def set_recursive_expression(self, expression):
        self.recursive_expression = expression
