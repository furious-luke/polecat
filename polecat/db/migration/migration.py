from psycopg2.sql import SQL

from ..decorators import dbcursor


class Migration:
    def __init__(self, operations, app=None):
        self.operations = operations
        self.app = app

    # def apply(self, schema):
    #     for operation in self.operations:
    #         operation.apply(schema)

    @property
    def forward_sql(self):
        sql, args = zip(*(op.sql for op in self.operations))
        return (SQL('\n\n').join(sql), sum(args, ()))

    @dbcursor
    def forward(self, cursor):
        if not getattr(self, '_applied', False):
            self._applied = True
            for dep in self.dependencies:
                dep.forward(cursor=cursor)
            cursor.execute(*self.forward_sql)
