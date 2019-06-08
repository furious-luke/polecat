from psycopg2.sql import Identifier

from ..query.query import Queryable

__all__ = ('Table', 'Column', 'RelatedColumn')

DBTYPE_INT = 'int'


class Table(Queryable):
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
        self.build()

    def __repr__(self):
        return f'<Table name="{self.name}">'

    # TODO: This is for making SQL expressions. It would be nice to
    # not have this here, as it's bleeding information between
    # abstractions.
    @property
    def alias(self):
        return self.name

    # TODO: This is for making SQL expressions. It would be nice to
    # not have this here, as it's bleeding information between
    # abstractions.
    def to_sql(self):
        return Identifier(self.name), ()

    def build(self):
        self.build_all_columns()

    def build_all_columns(self):
        for column in self.columns:
            self.build_column(column)

    def build_column(self, column):
        setattr(self.C, column.name, column)

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


class Column:
    def __init__(self, name, type, unique=False, null=True, primary_key=False):
        self.name = name
        self.type = type
        self.unique = unique
        self.null = null
        self.primary_key = primary_key

    def __repr__(self):
        return f'<Column name="{self.name}" type="{self.type}">'

    def to_db_value(self, value):
        return value

    def from_db_value(self, value):
        return value


class RelatedColumn(Column):
    def __init__(self, name, related_table, *args, **kwargs):
        super().__init__(name, DBTYPE_INT, *args, **kwargs)
        self.related_table = related_table

    def __repr__(self):
        return f'<RelatedColumn name="{self.name}" related_table="{self.related_table.name}">'


class ReverseColumn(RelatedColumn):
    pass
