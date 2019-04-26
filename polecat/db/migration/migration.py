import re
from pathlib import Path

from psycopg2.sql import SQL

from ...project.app import app_registry
from ...utils import indent
from ..decorators import dbcursor

migration_template = '''from polecat.db.migration.migration import Migration as BaseMigration
from polecat.db.migration.operation import CreateRole, CreateTable, GrantAccess
from polecat.db.migration.schema import Table, Role, Column, RelatedColumn


class Migration(BaseMigration):
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
        existing_migrations = self.find_existing_migrations()
        if existing_migrations:
            next_number = existing_migrations[-1][0] + 1
        else:
            next_number = 1
        return f'{next_number:04}_migration.py'

    @property
    def file_path(self):
        return self.migrations_path / self.filename

    @property
    def migrations_path(self):
        try:
            return app_registry[self.app].path / 'migrations'
        except TypeError:
            return Path('.') / 'migrations'

    @property
    def dependency_string(self):
        return f'{self.app}.{self.filename[:-3]}'

    def save(self):
        if not getattr(self, '_saved', False):
            self._saved = True
            Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w') as f:
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

    def find_existing_migrations(self):
        prog = re.compile(r'(\d{4})_[a-zA-Z_0-9]+\.py')
        path = self.migrations_path
        migrations = []
        try:
            for filename in path.iterdir():
                match = prog.match(filename.name)
                if match:
                    migrations.append((int(match.group(1)), filename.name))
        except FileNotFoundError:
            pass
        return sorted(migrations, key=lambda x: x[0])
