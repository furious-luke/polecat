from psycopg2.sql import Identifier

from ...utils.repr import to_repr
from .column import MutableColumn
from .entity import Entity

__all__ = ('Table',)


class Table(Entity):
    # TODO: These are here to support the Queryable interface. Bad
    # design, need to encapsulate these somewhere else.
    selectable = True
    mutatable = True

    def __init__(self, name, columns=None, checks=None, uniques=None,
                 access=None, indexes=None, app=None):
        # TODO: Unknown-unknown; cannot rename "name" or
        # polecat.db.query.selection.Selection will break. It expects
        # that if the column name passed in is not a string it has a
        # `.name` attribute.
        self.app = app
        self._name = name  # TODO: Not sure how I feel about this.
        self.columns = columns or []
        self.checks = checks or []
        self.uniques = uniques or []
        self.access = access
        self.indexes = indexes or []
        self.C = type('Columns', (), {})  # TODO
        self.schema = None

    def __repr__(self):
        return to_repr(
            self,
            app=self.app,
            name=self.name
        )

    @property
    def signature(self):
        return (Table, getattr(self.app, 'name', self.app), self.name)

    @property
    def name(self):
        name = self._name
        if self.app:
            name = f'{self.app.name.lower()}_{name}'
        return name

    def has_changed(self, other):
        return (
            getattr(self.app, 'name', self.app) != getattr(other.app, 'name', other.app) or
            self.name != other.name or
            self.checks != other.checks or
            self.uniques != other.uniques or
            self.have_columns_changed(other)
        )

    def have_columns_changed(self, other):
        # TODO: I don't think this is sufficient. I think I need to be
        # running "has_changed" on the columns in order to detect
        # variations to columns.
        from_columns = {
            column.name: column
            for column in self.iter_mutable_columns()
        }
        to_columns = {
            column.name: column
            for column in other.iter_mutable_columns()
        }
        return from_columns != to_columns

    # TODO: This is for making SQL expressions. It would be nice to
    # not have this here, as it's bleeding information between
    # abstractions.
    @property
    def alias(self):
        return self.name

    @property
    def root_relation(self):
        return self

    def add_column(self, column):
        self.columns.append(column)
        self.bind_column(column)

    def add_index(self, index):
        self.indexes.append(index)
        self.bind_index(index)

    # TODO: This is for making SQL expressions. It would be nice to
    # not have this here, as it's bleeding information between
    # abstractions.
    def to_sql(self):
        return Identifier(self.name), ()

    def bind(self, schema):
        if self.schema is None:
            self.schema = schema
            self.bind_all_columns()
            self.bind_all_indexes()

    def bind_all_columns(self):
        for column in self.columns:
            self.bind_column(column)

    def bind_column(self, column):
        setattr(self.C, column.name, column)
        column.bind(self)

    def bind_all_indexes(self):
        for index in self.indexes:
            self.bind_index(index)

    def bind_index(self, index):
        index.bind(self)

    def has_column(self, name):
        return hasattr(self.C, name)

    def get_column(self, name):
        try:
            return getattr(self.C, name)
        except AttributeError:
            raise KeyError(
                f'Column "{name}" does not exist on table "{self.name}"'
            )

    def iter_mutable_columns(self):
        for column in self.columns:
            if isinstance(column, MutableColumn):
                yield column

    def iter_column_names(self):
        for column in self.columns:
            yield column.name

    def get_subrelation(self, name):
        column = self.get_column(name)
        return column.related_table

    def push_selection(self, selection=None):
        pass
