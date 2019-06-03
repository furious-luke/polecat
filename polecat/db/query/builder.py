from .query import Common, Delete, Filter, Insert, Query, Select, Update
from .selection import Selection


class Q:
    @classmethod
    def common(cls, **subqueries):
        return Q(Common(subqueries))

    def __init__(self, queryable, branches=None):
        self.queryable = queryable
        self.branches = branches or []

    def select(self, *args, **kwargs):
        return Q(
            Select(self.queryable, Selection(*args, **kwargs)),
            branches=self.branches
        )

    def insert(self, *subquery, **values):
        source, branches = self.get_mutation_source()
        if len(subquery):
            if len(subquery) > 1:
                raise ValueError('Cannot pass more than on subquery')
            if len(values):
                raise ValueError('Cannot pass a subquery and keyword values')
            values, branches = merge_query_branches(subquery[0], branches)
        return Q(Insert(source, values), branches=branches)

    def insert_into(self, source, **values):
        return Q(
            Insert(source, values),
            branches=self.split_branch()
        )

    def update(self, **values):
        source, branches = self.get_mutation_source()
        return Q(Update(source, values), branches=branches)

    def update_into(self, source, **values):
        return Q(
            Update(source, values),
            branches=self.split_branch()
        )

    def delete(self):
        source, branches = self.get_mutation_source()
        return Q(Delete(source), branches=branches)

    def delete_from(self, source):
        return Q(
            Update(source),
            branches=self.split_branch()
        )

    def filter(self, **options):
        return Q(
            Filter(self.queryable, options),
            branches=self.branches
        )

    def get_mutation_source(self):
        if self.queryable.mutatable:
            source = self.queryable
            branches = None
        else:
            source = self.queryable.root
            branches = self.split_branch()
        return source, branches

    def split_branch(self):
        branches = self.branches
        if self.should_branch():
            branches.append(self.queryable)
        return branches

    def should_branch(self):
        return isinstance(self.queryable, Query)

    def iter_branches(self):
        for branch in self.branches:
            yield branch


def merge_query_branches(query, branches=None):
    queryable = query.queryable
    branches = (branches or []).extend(query.branches or [])
    return queryable, branches or None
