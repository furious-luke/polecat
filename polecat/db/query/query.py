from collections import defaultdict

from ..schema import RelatedColumn, ReverseColumn
from .selection import Selection


class Queryable:
    selectable = True
    mutatable = True


class Query(Queryable):
    def __init__(self, source=None):
        self.source = source

    @property
    def root(self):
        # TODO: I probably want to cache this?
        return getattr(self.source, 'root', self.source)

    def assert_selectable(self, queryable):
        if not getattr(queryable, 'selectable', False):
            raise ValueError(f'Queryable is not selectable {queryable}')

    def assert_mutatable(self, queryable):
        if not getattr(queryable, 'mutatable', False):
            raise ValueError(f'Queryable is not mutatable {queryable}')


class Select(Query):
    mutatable = False

    def __init__(self, source, selection, **kwargs):
        super().__init__(source, **kwargs)
        self.assert_selectable(source)
        self.selection = selection

    def iter_column_names(self):
        return iter(self.selection)

    def has_column(self, name):
        return self.selection.has_column(name)


class Insert(Query):
    mutatable = False

    def __init__(self, source, values, **kwargs):
        super().__init__(source, **kwargs)
        self.reverse_queries = defaultdict(list)
        values = self.coerce_values(values)
        self.assert_mutatable(source)
        self.assert_selectable(values)
        self.assert_values_match_columns(values)
        self.values = values

    def iter_column_names(self):
        return iter(self.source.iter_column_names())

    def has_column(self, name):
        return self.source.has_column(name)

    def get_column(self, name):
        return self.source.get_column(name)

    def coerce_values(self, values):
        if isinstance(values, dict):
            return self.dict_to_values(values)
        else:
            return values

    def dict_to_values(self, values):
        mapped_values = {}
        for column_name, subvalue in values.items():
            column = self.get_column(column_name)
            # TODO: It would be nice to avoid breaking the OCP here.
            if isinstance(column, RelatedColumn):
                subvalue = self.subvalues_to_subquery(column, subvalue)
            elif isinstance(column, ReverseColumn):
                self.create_reverse_queries(column, subvalue)
                continue
            mapped_values[column_name] = subvalue
        return Values(mapped_values)

    def subvalues_to_subquery(self, column, subvalues):
        if isinstance(subvalues, Query):
            return subvalues
        # TODO: Ugh, this is soooo bad. This is how I'm currently
        # handing being given an integer for the primary key.
        if isinstance(subvalues, int):
            return subvalues
        # TODO: Should we be considering if there's an ID in the
        # subset? If so this should be an Update instead of a Insert.
        return Select(
            Insert(column.related_table, subvalues),
            Selection('id')
        )

    def create_reverse_queries(self, column, linked_values):
        related_column = column.related_column
        for values in linked_values:
            reverse_query = Insert(
                column.related_table,
                {
                    **values,
                    related_column.name: Select(self, Selection('id'))
                }
            )
            self.reverse_queries[column.name].append(reverse_query)

    def assert_values_match_columns(self, values):
        for column_name in values.iter_column_names():
            # TODO: This assumes the source has the `has_column`
            # method. Should we formalise this in an interface?
            if not self.source.has_column(column_name):
                raise ValueError(f'Invalid column "{column_name}" name in insert')


class Update(Insert):
    def assert_mutatable(self, source):
        # TODO: Think about this more, but Update can work with pretty
        # much anything. Maybe need "is_insertable" and "is_updatable"?
        return True


class Delete(Query):
    mutatable = False

    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)
        self.assert_mutatable(source)

    def iter_column_names(self):
        return iter(self.source.iter_column_names())

    def has_column(self, name):
        return self.source.has_column(name)


class Filter(Query):
    mutatable = False

    def __init__(self, source, options, **kwargs):
        super().__init__(source, **kwargs)
        self.assert_selectable(source)
        self.options = options

    def has_column(self, name):
        return self.source.has_column(name)

    def get_column(self, name):
        return self.source.get_column(name)


class Common(Query):
    mutatable = False

    def __init__(self, subqueries):
        super().__init__()
        self.subqueries = subqueries


class Values(Query):
    mutatable = False

    def __init__(self, values, **kwargs):
        super().__init__(**kwargs)
        self.values = values

    def iter_items(self):
        return self.values.items()

    def iter_column_names(self):
        return iter(self.values)
