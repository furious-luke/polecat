from psycopg2.sql import SQL, Identifier

from .expression import Expression


class Delete(Expression):
    def __init__(self, relation, returning=None, where=None):
        self.relation = relation
        self.returning = returning or ()
        self.where = where

    def to_sql(self):
        if self.returning:
            returning_sql = SQL(' RETURNING {}').format(
                map(Identifier, self.returning)
            )
        else:
            returning_sql = SQL('')
        where_sql, where_args = self.get_where_sql()
        return (
            SQL('DELETE FROM {}{}{}').format(
                Identifier(self.relation.name),
                returning_sql,
                where_sql
            ),
            where_args
        )

    def get_where_sql(self):
        if self.where:
            sql, args = self.where.get_sql(self.relation)
            return SQL(' WHERE {}').format(sql), args
        else:
            return SQL(''), ()

    def push_selection(self, selection=None):
        pass
