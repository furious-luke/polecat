from polecat.db.schema.utils import Auto
from psycopg2.sql import SQL, Identifier

from ...core.registry import MappedRegistry, RegistryMetaclass
from .. import schema

__all__ = ('Column', 'IntColumn')

MappedRegistry('migration_column_registry')


class Column(metaclass=RegistryMetaclass):
    _registry = 'migration_column_registry'
    dbtype = None

    def __init__(self, schema_column):
        self.schema_column = schema_column

    def to_sql(self):
        col = self.schema_column
        constraints_sql, args = self.get_constraints_sql()
        parts = [
            Identifier(col.name),
            self.get_type_sql(),
            constraints_sql
        ]
        return SQL(' ').join(parts), args

    def get_constraints_sql(self):
        constraints = []
        args = ()
        col = self.schema_column
        if col.primary_key:
            constraints.append('PRIMARY KEY')
        else:
            if not col.null:
                constraints.append('NOT NULL')
            if col.unique:
                constraints.append('UNIQUE')
            if col.default is not None:
                constraints.append('DEFAULT %s')
                args += (self.translate_default_value(col.default),)
        return SQL(' '.join(constraints)), args

    def get_type_sql(self):
        return SQL(self.dbtype)

    def translate_default_value(self, value):
        return value


class IntColumn(Column):
    sources = (schema.IntColumn,)
    dbtype = 'int'


class FloatColumn(Column):
    sources = (schema.FloatColumn,)
    dbtype = 'real'


class SerialColumn(Column):
    sources = (schema.SerialColumn,)
    dbtype = 'serial'


class TextColumn(Column):
    sources = (schema.TextColumn,)
    dbtype = 'text'

    def get_type_sql(self):
        col = self.schema_column
        if col.max_length:
            return SQL(f'varchar({col.max_length})')
        else:
            return SQL(self.dbtype)


class PasswordColumn(TextColumn):
    sources = (schema.PasswordColumn,)
    dbtype = 'chkpass'


class TimestampColumn(Column):
    sources = (schema.TimestampColumn,)
    dbtype = 'timestamptz'

    def translate_default_value(self, value):
        if value == Auto:
            return 'now()'
        else:
            return value


class RelatedColumn(IntColumn):
    sources = (schema.RelatedColumn,)

    def to_sql(self):
        col = self.schema_column
        constraints_sql, args = self.get_constraints_sql()
        parts = [
            Identifier(col.name),
            self.get_type_sql(),
            self.get_reference_sql(),
            constraints_sql
        ]
        return SQL(' ').join(parts), args

    def get_reference_sql(self):
        col = self.schema_column
        return SQL('REFERENCES {}({})').format(
            Identifier(getattr(col.related_table, 'name', col.related_table)),
            Identifier('id')
        )
