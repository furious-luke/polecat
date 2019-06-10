from ..connection import cursor as cursor_context  # TODO: Ugh.
from ..decorators import dbcursor
from .query import Common, Delete, Filter, Insert, Query, Select, Update
from .selection import Selection


class Q:
    def __init__(self, queryable, branches=None):
        self.queryable = queryable
        self.branches = branches or []

    def __iter__(self):
        with cursor_context() as cursor:
            self.execute(cursor=cursor)
            for row in cursor:
                yield row

    @classmethod
    def common(cls, *subqueries):
        return Q(Common(subqueries))

    @dbcursor
    def to_sql(self, cursor):
        # TODO: This is also technically outside of the scope of this
        # class.
        from ..sql2.strategy import Strategy
        strategy = Strategy()
        expr = strategy.parse(self)
        return cursor.mogrify(*expr.to_sql())

    @dbcursor
    def execute(self, cursor):
        # TODO: This is pretty bad. How to keep this purely as a
        # builder, but also inject strategy and execution knowledge
        # for convenience?
        from ..sql2.strategy import Strategy
        strategy = Strategy()
        expr = strategy.parse(self)
        sql, args = expr.to_sql()
        print(cursor.mogrify(sql, args))
        cursor.execute(sql, args)

    def select(self, *args, **kwargs):
        return self.chain(
            Select(self.queryable, Selection(*args, **kwargs)),
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
            self.branches.extend(insert.reverse_queries)
            # TODO: Do I need to wrap insert in a select?
        return self.chain(insert)

    def insert_into(self, source, **values):
        self.split_branch()
        return self.chain(
            Insert(source, values)
        )

    def update(self, *subquery, **values):
        source = self.get_mutation_source()
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

    def parse_value_dict(self, queryable, values):
        parsed_values = {}
        for column_name, value in values.items():
            if isinstance(value, Q):
                queryable = self.merge_query_branches(value)
                value = queryable
            parsed_values[column_name] = value
        return parsed_values

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
        return self.__class__(queryable, self.branches)

    def merge_query_branches(self, query):
        queryable = query.queryable
        self.branches = (self.branches or []).extend(query.branches or [])
        return queryable
