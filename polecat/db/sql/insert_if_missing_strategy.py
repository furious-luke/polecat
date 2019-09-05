from psycopg2.sql import SQL, Placeholder

from .expression.exists import Exists
from .expression.expression import Expression
from .expression.insert import Insert
from .expression.not_ import Not
from .expression.select import Select
from .expression.subquery import Subquery
from .expression.union import Union
from .expression.where import Where
from .insert_strategy import InsertStrategy


# TODO: This class should be merged into Select.
class DummySelect(Expression):
    def __init__(self, values, where):
        self.values = values
        self.where = where

    def to_sql(self):
        where_sql, where_args = self.where.to_sql()
        # TODO: This is all wrong, need to think more clearly about
        # this.
        values_sql = []
        values_args = ()
        for value in self.values.values():
            if isinstance(value, Expression):
                sql, args = value.to_sql()
                values_sql.append(sql)
                values_args += args
            else:
                values_sql.append(Placeholder())
                values_args += (value,)
        values_sql = SQL(', ').join(values_sql)
        return (
            SQL('SELECT {} WHERE {}').format(
                values_sql,
                where_sql
            ),
            values_args + where_args
        )

    def iter_column_names(self):
        return self.values.keys()


class InsertIfMissingStrategy(InsertStrategy):
    def __init__(self, root_strategy):
        self.root = root_strategy
        self.relation_counter = 0

    def parse_query(self, query):
        parsed_values = self.parse_values(query, query.values)
        # TODO: This is pretty awful.
        parsed_values = parsed_values.values.as_dict()
        values = {
            **query.defaults,
            **parsed_values
        }
        where_expr = Where(**parsed_values)
        insert_expr = Insert(
            query.source,
            DummySelect(
                values,
                where=Not(
                    Exists(
                        Subquery(
                            Select(
                                query.source,
                                (SQL('1'),),
                                where=where_expr
                            )
                        )
                    )
                )
            )
        )
        alias = self.root.create_alias(insert_expr)
        expr = Union([
            Select(alias),
            Select(
                query.source,
                ('id',),  # TODO: Wat...
                where=where_expr
            )
        ])
        return expr
