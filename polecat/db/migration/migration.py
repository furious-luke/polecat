from psycopg2.sql import SQL

from ...project.app import app_registry
from ...utils import indent
from ..decorators import dbcursor

migration_template = '''from polecat.db.migration.migration import Migration
from polecat.db.migration.operation import *  # noqa
from polecat.db.migration.schema import *  # noqa

class Migration:
    dependencies = [{}]
    operations = [{}]
'''


class Migration:
    def __init__(self, operations=None, app=None, dependencies=None):
        self.operations = operations or getattr(self, 'operations', [])
        self.app = app
        self.dependencies = dependencies or getattr(self, 'dependencies', [])

    # def apply(self, schema):
    #     for operation in self.operations:
    #         operation.apply(schema)

    @property
    def forward_sql(self):
        sql, args = zip(*(op.sql for op in self.operations))
        return (SQL('\n\n').join(sql), sum(args, ()))

    @dbcursor
    def forward(self, cursor):
        if not getattr(self, '_applied', False):
            self._applied = True
            for dep in self.dependencies:
                dep.forward(cursor=cursor)
            cursor.execute(*self.forward_sql)

    @property
    def filename(self):
        filename = '0001_initial.py'
        return filename

    @property
    def file_path(self):
        return app_registry[self.app].path / 'migrations' / self.filename

    @property
    def dependency_string(self):
        return f'{self.app}.{self.filename[:-3]}'

    def save(self):
        if not getattr(self, '_saved', False):
            self._saved = True
            with open(self.filename, 'w') as f:
                f.write(self.serialize())

    def serialize(self):
        dep_strs = []
        for dep in self.dependencies:
            dep.save()
            dep_strs.append(dep.dependency_string)
        dep_strs = ',\n'.join(dep_strs)
        if dep_strs:
            dep_strs = indent(f'\n{dep_strs}', 8)
            dep_strs += indent('\n')
        op_strs = []
        for op in self.operations:
            op_strs.append(op.serialize())
        op_strs = ',\n'.join(op_strs)
        if op_strs:
            op_strs = indent(f'\n{op_strs}', 8)
            op_strs += indent('\n')
        return migration_template.format(dep_strs, op_strs)
