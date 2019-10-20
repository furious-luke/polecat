import logging

from polecat.core.config import default_config

from ..connection import cursor as cursor_context  # TODO: Ugh.
from ..decorators import dbcursor
from .query import (Common, Delete, Filter, Insert, InsertIfMissing, Join,
                    Query, Select, Update, Values)
from .selection import Selection

logger = logging.getLogger(__name__)


class Q:
    def __init__(self, queryable=None, branches=None, session=None):
        self.queryable = queryable
        self.branches = branches or []
        self.session = session
        self.row_count = 0

    def __iter__(self):
        with cursor_context() as cursor:
            self.execute(cursor=cursor)
            for row in cursor:
                yield row[0]

    def __len__(self):
        # TODO: If we haven't executed, we probably should?
        return self.row_count

    def get(self):
        with cursor_context() as cursor:
            self.execute(cursor=cursor)
            if cursor.rowcount == 0:
                return None
            elif cursor.rowcount > 1:
                # TODO: Better exception.
                raise Exception('Multiple results for get query.')
            for row in cursor:
                return row[0]

    @classmethod
    def common(cls, *subqueries):
        return Q(Common(subqueries))

    @dbcursor
    def to_sql(self, cursor):
        # TODO: This is also technically outside of the scope of this
        # class.
        from ..sql.strategy import Strategy
        strategy = Strategy()
        expr = strategy.parse(self)
        return cursor.mogrify(*expr.to_sql())

    @dbcursor()
    def execute(self, cursor):
        # TODO: This is pretty bad. How to keep this purely as a
        # builder, but also inject strategy and execution knowledge
        # for convenience?
        from ..sql.strategy import Strategy
        strategy = Strategy()
        expr = strategy.parse(self)
        sql, args = expr.to_sql()
        if default_config.log_sql:
            # TODO: Get my logging sorted.
            # logger.debug(cursor.mogrify(sql, args))
            print(cursor.mogrify(sql, args))
        cursor.execute(sql, args)
        self.row_count = cursor.rowcount

    def select(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], Selection):
            if len(kwargs):
                raise ValueError('Cannot pass a Selection instance and lookups.')
            selection = args[0]
        else:
            selection = Selection(*args, **kwargs)
        return self.chain(
            Select(self.queryable, selection)
        )

    def insert(self, *subquery, **values):
        source = self.get_mutation_source()
        if len(subquery):
            if len(subquery) > 1:
                raise ValueError('Cannot pass more than one subquery')
            if len(values):
                raise ValueError('Cannot pass a subquery and keyword values')
            values = self.merge_query_branches(subquery[0])
        else:
            values = self.parse_value_dict(self.queryable, values)
        insert = Insert(source, values)
        if insert.reverse_queries:
            if self.branches is None:
                self.branches = []
            for reverse_queries in insert.reverse_queries.values():
                self.branches.extend(reverse_queries)
            # TODO: Do I need to wrap insert in a select?
        return self.chain(insert)

    def bulk_insert(self, columns, values):
        source = self.get_mutation_source()
        values = self.parse_bulk_values(columns, values)
        insert = Insert(source, values)
        if insert.reverse_queries:
            if self.branches is None:
                self.branches = []
            for reverse_queries in insert.reverse_queries.values():
                self.branches.extend(reverse_queries)
            # TODO: Do I need to wrap insert in a select?
        return self.chain(insert)

    def insert_into(self, source, **values):
        self.split_branch()
        return self.chain(
            Insert(source, values)
        )

    def insert_if_missing(self, values, defaults={}):
        source = self.get_mutation_source()
        values = self.parse_value_dict(self.queryable, values)
        defaults = self.parse_value_dict(self.queryable, defaults)
        insert = InsertIfMissing(source, values, defaults)
        # TODO: Do I need to worry about reverse queries?
        return self.chain(insert)

    def update(self, *subquery, **values):
        # TODO: Need to think about this more, but an Update is almost
        # always able to run, regardless of the mutability of the
        # source.
        source = self.queryable
        # TODO: This is duped in insert.
        if len(subquery):
            if len(subquery) > 1:
                raise ValueError('Cannot pass more than one subquery')
            if len(values):
                raise ValueError('Cannot pass a subquery and keyword values')
            values = self.merge_query_branches(subquery[0])
        else:
            values = self.parse_value_dict(self.queryable, values)
        return self.chain(Update(source, values))

    def update_into(self, source, **values):
        self.split_branch()
        return self.chain(Update(source, values))

    def delete(self):
        # TODO: Would be good to remove this conditional.
        if isinstance(self.queryable, Filter):
            source = self.queryable
        else:
            source = self.get_mutation_source()
        return self.chain(Delete(source))

    def delete_from(self, source):
        self.split_branch()
        return self.chain(Update(source))

    def filter(self, **options):
        return self.chain(Filter(self.queryable, options))

    def recurse(self, column):
        # TODO: This is clearly wrong. It mutates the query, possibly
        # effecting other uses.
        assert isinstance(self.queryable, Select)
        self.queryable.recurse_column = column
        return self

    def limit(self, limit):
        # TODO: This is clearly wrong. It mutates the query, possibly
        # effecting other uses.
        assert isinstance(self.queryable, Select)
        self.queryable.limit = limit
        return self

    def order(self, columns):
        # TODO: This is clearly wrong. It mutates the query, possibly
        # effecting other uses.
        assert isinstance(self.queryable, Select)
        self.queryable.order = columns
        return self

    def join(self, separator=' '):
        return self.chain(
            Join(self.queryable, separator)
        )

    def branch(self, query):
        if self.queryable is not None:
            self.branches.append(self.queryable)
        self.branches.extend(query.branches)
        return self.chain(query.queryable)

    def parse_value_dict(self, queryable, values):
        parsed_values = {}
        for column_name, value in values.items():
            if isinstance(value, Q):
                queryable = self.merge_query_branches(value)
                value = queryable
            parsed_values[column_name] = self.parse_value(queryable, column_name, value)
        return parsed_values

    def parse_bulk_values(self, columns, values):
        return Values(values, columns)

    def parse_value(self, queryable, column_name, value):
        return value

    def get_mutation_source(self):
        if self.queryable.mutatable:
            source = self.queryable
        else:
            source = self.queryable.root
            self.split_branch()
        return source

    def split_branch(self):
        if self.should_branch():
            self.branches.append(self.queryable)

    def should_branch(self):
        return isinstance(self.queryable, Query)

    def iter_branches(self):
        for branch in self.branches:
            yield branch

    def chain(self, queryable):
        return self.__class__(queryable, self.branches, session=self.session)

    def merge_query_branches(self, query):
        queryable = query.queryable
        self.branches = (self.branches or []) + (query.branches or [])
        return queryable
