from psycopg2.sql import SQL, Identifier

from .expression import Expression


class Alias(Expression):
    def __init__(self, term, column=None):
        super().__init__(term)
        self.expression = self.term  # TODO: Deprecate
        self.column = column

    # TODO: Deprecate
    @property
    def alias(self):
        return self.expression.alias

    def to_sql(self):
        if self.column:
            column_sql = SQL('.{}').format(Identifier(self.column))
        else:
            column_sql = SQL('')
        return (
            SQL('{}{}').format(
                Identifier(self.alias),
                column_sql
            ),
            ()
        )
