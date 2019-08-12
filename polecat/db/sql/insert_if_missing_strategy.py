from psycopg2.sql import SQL

from .expression.exists import Exists
from .expression.expression import Expression
from .expression.insert import Insert
from .expression.not_ import Not
from .expression.select import Select
from .expression.subquery import Subquery
from .expression.where import Where
from .insert_strategy import InsertStrategy


# TODO: This class should be merged into Select.
class DummySelect(Expression):
    def __init__(self, values, where):
        self.values = values
        self.where = where

    def to_sql(self):
        where_sql, where_args = self.where.to_sql()
        values_str = ', '.join(['%s']*len(self.values))
        return (
            SQL('SELECT %s WHERE {}' % values_str).format(
                where_sql
            ),
            tuple(self.values.values()) + where_args
        )

    def iter_column_names(self):
        return self.values.keys()


class InsertIfMissingStrategy(InsertStrategy):
    def __init__(self, root_strategy):
        self.root = root_strategy
        self.relation_counter = 0

    def parse_query(self, query):
        values = {
            **query.defaults,
            **query.values.values
        }
        expr = Insert(
            query.source,
            DummySelect(
                values,
                where=Not(
                    Exists(
                        Subquery(
                            Select(
                                query.source,
                                (SQL('1'),),
                                where=Where(
                                    **query.values.values
                                )
                            )
                        )
                    )
                )
            )
        )
        return expr
