from psycopg2.sql import SQL, Identifier


class Join:
    LEFT = 'LEFT'

    def __init__(self, expression, join_type=None, alias=None, condition=None):
        self.expression = expression
        self.join_type = join_type
        self.alias = alias
        self.condition = condition

    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        if self.join_type is None:
            return SQL(', {}').format(expr_sql), expr_args
        join_type = self.get_join_type_fragment()
        cond_sql, cond_args = self.get_condition_sql()
        alias_sql = self.get_alias_sql()
        return (
            SQL('%sJOIN {}{}{}' % join_type).format(
                expr_sql,
                alias_sql,
                cond_sql
            ),
            expr_args + cond_args
        )

    def get_join_type_fragment(self):
        join_type = self.join_type
        if join_type:
            join_type += ' '
        return join_type

    def get_alias_sql(self):
        if self.alias:
            return SQL(' AS {}').format(Identifier(self.alias))
        else:
            return SQL('')

    def get_condition_sql(self):
        if self.condition:
            cond_sql, cond_args = self.condition.to_sql()
            return (
                SQL(' ON {}').format(cond_sql),
                cond_args
            )
        else:
            return SQL(''), ()

    def push_selection(self, selection=None):
        self.expression.push_selection(selection=selection)


class LateralJoin(Join):
    def to_sql(self):
        expr_sql, expr_args = self.expression.to_sql()
        join_type = self.get_join_type_fragment()
        cond_sql, cond_args = self.get_condition_sql()
        return (
            SQL('%sJOIN LATERAL ({}) AS {}{}' % join_type).format(
                expr_sql,
                Identifier(self.alias),
                cond_sql
            ),
            expr_args + cond_args
        )
