class Executor:
    def __init__(self, expression, cursor):
        self.expression = expression
        self.cursor = cursor

    def execute(self, cursor):
        sql, args = self.expression.to_sql()
        cursor.execute(sql, args)
        for row in cursor:
            yield row
