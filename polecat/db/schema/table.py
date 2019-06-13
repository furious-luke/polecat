from psycopg2.sql import Identifier

from ...utils.repr import to_repr

__all__ = ('Table',)


class Table:
    # TODO: These are here to support the Queryable interface. Bad
    # design, need to encapsulate these somewhere else.
    selectable = True
    mutatable = True

    def __init__(self, name, columns=None, checks=None, uniques=None,
                 access=None):
        # TODO: Unknown-unknown; cannot rename "name" or
        # polecat.db.query.selection.Selection will break. It expects
        # that if the column name passed in is not a string it has a
        # `.name` attribute.
        self.name = name
        self.columns = columns or []
        self.checks = checks or []
        self.uniques = uniques or []
        self.access = access
        self.C = type('Columns', (), {})  # TODO
        self.schema = None

    def __repr__(self):
        return to_repr(
            self,
            name=self.name
        )

    # TODO: This is for making SQL expressions. It would be nice to
    # not have this here, as it's bleeding information between
    # abstractions.
    @property
    def alias(self):
        return self.name

    def add_column(self, column):
        self.columns.append(column)
        self.bind_column(column)

    # TODO: This is for making SQL expressions. It would be nice to
    # not have this here, as it's bleeding information between
    # abstractions.
    def to_sql(self):
        return Identifier(self.name), ()

    def bind(self, schema):
        if self.schema is None:
            self.schema = schema
            self.bind_all_columns()

    def bind_all_columns(self):
        for column in self.columns:
            self.bind_column(column)

    def bind_column(self, column):
        setattr(self.C, column.name, column)
        column.bind(self)

    def has_column(self, name):
        return hasattr(self.C, name)

    def get_column(self, name):
        try:
            return getattr(self.C, name)
        except AttributeError:
            raise KeyError(
                f'Column "{name}" does not exist on table "{self.name}"'
            )

    def iter_column_names(self):
        for column in self.columns:
            yield column.name

    def get_subrelation(self, name):
        column = self.get_column(name)
        return column.related_table

    def push_selection(self, selection=None):
        pass
