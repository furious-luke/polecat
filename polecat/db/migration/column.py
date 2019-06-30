from psycopg2.sql import SQL, Identifier

from .. import schema
from ...core.registry import MappedRegistry, RegistryMetaclass

__all__ = ('Column', 'IntColumn')

MappedRegistry('migration_column_registry')


class Column(metaclass=RegistryMetaclass):
    _registry = 'migration_column_registry'
    dbtype = None

    def __init__(self, schema_column):
        self.schema_column = schema_column

    def to_sql(self):
        col = self.schema_column
        parts = [
            Identifier(col.name),
            self.get_type_sql(),
            self.get_constraints_sql()
        ]
        return SQL(' ').join(parts)

    def get_constraints_sql(self):
        constraints = []
        col = self.schema_column
        if col.primary_key:
            constraints.append('PRIMARY KEY')
        else:
            if not col.null:
                constraints.append('NOT NULL')
            if col.unique:
                constraints.append('UNIQUE')
        return SQL(' '.join(constraints))

    def get_type_sql(self):
        return SQL(self.dbtype)


class IntColumn(Column):
    sources = (schema.IntColumn,)
    dbtype = 'int'


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


class TimestampColumn(Column):
    sources = (schema.TimestampColumn,)
    dbtype = 'timestamptz'


class RelatedColumn(IntColumn):
    sources = (schema.RelatedColumn,)

    def to_sql(self):
        col = self.schema_column
        parts = [
            Identifier(col.name),
            self.get_type_sql(),
            self.get_reference_sql(),
            self.get_constraints_sql()
        ]
        return SQL(' ').join(parts)

    def get_reference_sql(self):
        col = self.schema_column
        return SQL('REFERENCES {}({})').format(
            Identifier(getattr(col.related_table, 'name', col.related_table)),
            Identifier('id')
        )
