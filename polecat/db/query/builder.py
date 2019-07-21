import logging

from polecat.core.context import active_context

from ..connection import cursor as cursor_context  # TODO: Ugh.
from ..decorators import dbcursor
from .query import Common, Delete, Filter, Insert, Query, Select, Update
from .selection import Selection

logger = logging.getLogger(__name__)


class Q:
    def __init__(self, queryable, branches=None, session=None):
        self.queryable = queryable
        self.branches = branches or []
        self.session = session

    def __iter__(self):
        with cursor_context(autocommit=False) as cursor:
            self.execute(cursor=cursor)
            for row in cursor:
                yield row[0]

    def get(self):
        with cursor_context(autocommit=False) as cursor:
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

    @dbcursor(autocommit=False)
    def execute(self, cursor):
        ctx = active_context()
        # TODO: This is pretty bad. How to keep this purely as a
        # builder, but also inject strategy and execution knowledge
        # for convenience?
        from ..sql.strategy import Strategy
        strategy = Strategy()
        expr = strategy.parse(self)
        sql, args = expr.to_sql()
        if ctx.config.log_sql:
            # TODO: Get my logging sorted.
            # logger.debug(cursor.mogrify(sql, args))
            print(cursor.mogrify(sql, args))
        cursor.execute(sql, args)
        # TODO: This is strange. For some reason I need to commit
        # the outcome of the query here. If I don't, then the
        # changes are somehow lost.
        cursor.connection.commit()

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

    def insert_into(self, source, **values):
        self.split_branch()
        return self.chain(
            Insert(source, values)
        )

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
        source = self.get_mutation_source()
        return self.chain(Delete(source))

    def delete_from(self, source):
        self.split_branch()
        return self.chain(Update(source))

    def filter(self, **options):
        return self.chain(Filter(self.queryable, options))

    def branch(self, query):
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
        self.branches = (self.branches or []).extend(query.branches or [])
        return queryable
