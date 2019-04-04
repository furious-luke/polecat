from psycopg2.sql import SQL

from ..decorators import dbcursor


class Migration:
    def __init__(self, operations):
        self.operations = operations

    @dbcursor
    def forward(self, cursor):
        cursor.execute(*self.forward_sql())

    def forward_sql(self):
        sql, args = zip(*(op.forward_sql() for op in self.operations))
        return (SQL('\n\n').join(sql), sum(args, ()))
