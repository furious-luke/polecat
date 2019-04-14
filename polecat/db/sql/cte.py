from psycopg2.sql import SQL, Identifier


class CTE:
    def __init__(self, sql, args, before=None):
        self.sql = sql
        self.args = args
        self.after = None
        self.before = before
        if before:
            before.after = self
        self.id = before.next_id if before else 0
        self.next_id = self.id + 1
        self.alias = f'cte{self.id}'

    def evaluate(self):
        sql, args = SQL('{} AS ({})').format(Identifier(self.alias), self.sql), self.args
        if self.after:
            asql, aargs = self.after.evaluate()
            sql, args = SQL('{}, {}').format(sql, asql), args + aargs
        return sql, args
