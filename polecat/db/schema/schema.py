from psycopg2.sql import Identifier

__all__ = ('Table', 'Column', 'RelatedColumn', 'ReverseColumn')

DBTYPE_INT = 'int'


class Table:
    selectable = True
    mutatable = True
    registry = {}

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
        self.registry[self.name] = self

    def __repr__(self):
        return f'<Table name="{self.name}">'

    @classmethod
    def bind_all_tables(cls):
        for table in cls.registry.values():
            table.bind_all_columns()

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


class Column:
    def __init__(self, name, type, unique=False, null=True, primary_key=False):
        self.name = name
        self.type = type
        self.unique = unique
        self.null = null
        self.primary_key = primary_key

    def __repr__(self):
        return f'<Column name="{self.name}" type="{self.type}">'

    def bind(self, table):
        pass

    def to_db_value(self, value):
        return value

    def from_db_value(self, value):
        return value


class RelatedColumn(Column):
    def __init__(self, name, related_table, *args, related_column=None,
                 **kwargs):
        super().__init__(name, DBTYPE_INT, *args, **kwargs)
        self.related_table = related_table
        self.related_column = related_column

    def __repr__(self):
        return (
            f'<RelatedColumn name="{self.name}"'
            f' related_table="{self.related_table.name}">'
        )

    def bind(self, table):
        if self.should_bind_related_table():
            self.bind_related_table()
        if self.should_bind_related_column():
            self.bind_related_column(table)

    def should_bind_related_table(self):
        return isinstance(self.related_table, str)

    def bind_related_table(self):
        self.related_table = Table.registry[self.related_table]

    def should_bind_related_column(self):
        return self.related_column and isinstance(self.related_column, str)

    def bind_related_column(self, table):
        self.related_column = ReverseColumn(
            self.related_column,
            table,
            self
        )
        self.related_table.add_column(self.related_column)


class ReverseColumn:
    def __init__(self, name, related_table, related_column):
        self.name = name
        self.related_table = related_table
        self.related_column = related_column

    def __repr__(self):
        return (
            f'<ReverseColumn name="{self.name}"'
            f' related_table="{self.related_table.name}">'
        )

    def bind(self, table):
        pass
