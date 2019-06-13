from ...utils.repr import to_repr
from .table import Table

__all__ = ('Column', 'MutableColumn', 'IntColumn', 'TextColumn',
           'BoolColumn', 'FloatColumn', 'RelatedColumn', 'ReverseColumn',
           'PasswordColumn', 'TimestampColumn', 'UUIDColumn')


class Column:
    def __init__(self, name, unique=False):
        self.name = name
        self.unique = unique

    def __repr__(self):
        return to_repr(
            self,
            name=self.name
        )

    def bind(self, table):
        self.table = table

    def to_db_value(self, value):
        return value

    def from_db_value(self, value):
        return value


class MutableColumn(Column):
    def __init__(self, name, null=True, primary_key=False, **kwargs):
        super().__init__(name, **kwargs)
        self.null = null
        self.primary_key = primary_key

    def __repr__(self):
        return to_repr(
            self,
            name=self.name
        )


class IntColumn(MutableColumn):
    pass


class FloatColumn(MutableColumn):
    pass


class BoolColumn(MutableColumn):
    pass


class TextColumn(MutableColumn):
    def __init__(self, *args, max_length=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_length = max_length


class PasswordColumn(TextColumn):
    pass


class TimestampColumn(MutableColumn):
    pass


class UUIDColumn(MutableColumn):
    pass


class RelatedColumn(IntColumn):
    def __init__(self, name, related_table, *args, related_column=None,
                 **kwargs):
        super().__init__(name, *args, **kwargs)
        self.related_table = related_table
        self.related_column = related_column

    def __repr__(self):
        return to_repr(
            self,
            name=self.name,
            related_table=self.related_table.name
        )

    def bind(self, table):
        super().bind(table)
        if self.should_bind_related_table():
            self.bind_related_table()
        if self.should_bind_related_column():
            self.bind_related_column(table)

    def should_bind_related_table(self):
        return isinstance(self.related_table, str)

    def bind_related_table(self):
        self.related_table = self.table.schema.get_table_by_name(
            self.related_table
        )

    def should_bind_related_column(self):
        return self.related_column and isinstance(self.related_column, str)

    def bind_related_column(self, table):
        self.related_column = ReverseColumn(
            self.related_column,
            table,
            self
        )
        self.related_table.add_column(self.related_column)


class ReverseColumn(Column):
    def __init__(self, name, related_table, related_column):
        self.name = name
        self.related_table = related_table
        self.related_column = related_column

    def __repr__(self):
        return to_repr(
            self,
            name=self.name,
            related_table=self.related_table
        )
