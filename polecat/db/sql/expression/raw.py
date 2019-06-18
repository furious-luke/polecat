from .expression import Expression


class RawSQL(Expression):
    def __init__(self, sql, args=None):
        self.sql = sql
        self.args = args or ()

    def to_sql(self):
        return self.sql, self.args
