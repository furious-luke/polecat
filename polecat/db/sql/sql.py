from ..connection import cursor


class Sql:
    def __init__(self, sql, args=None):
        if isinstance(sql, tuple):
            self.sql = sql[0]
            self.args = sql[1]
        else:
            self.sql = sql
            self.args = args or ()

    def __str__(self):
        with cursor() as curs:
            return curs.mogrify(self.sql, self.args).decode()
