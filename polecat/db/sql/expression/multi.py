from psycopg2.sql import SQL

from .expression import Expression


class Multi(Expression):
    def __init__(self, *expressions):
        self.expressions = expressions

    def to_sql(self):
        all_sql = []
        all_args = ()
        for expr in self.expressions:
            sql, args = expr.to_sql()
            all_sql.append(sql)
            all_args += args
        return SQL('; ').join(all_sql), all_args
