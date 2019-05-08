import re
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from psycopg2.sql import SQL

from ...utils import indent
from ..decorators import dbcursor
from ..connection import transaction
from .utils import project_migrations_path

migration_template = '''from polecat.db.migration.migration import Migration as BaseMigration
from polecat.db.migration.operation import CreateRole, CreateTable, GrantAccess, CreateExtension
from polecat.db.migration.schema import Table, Role, Column, RelatedColumn


class Migration(BaseMigration):
    dependencies = [{}]
    operations = [{}]
'''


class Migration:
    filename_prog = re.compile(r'(\d{4})_[a-zA-Z_0-9]+\.py')

    @classmethod
    def load_migration_class(cls, path, app=None):
        module_path = path.name[:-3]
        if app:
            module_path = f'{app}.{module_path}'
        spec = spec_from_file_location(module_path, str(path))
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.Migration

    def __init__(self, operations=None, app=None, dependencies=None, name=None):
        self.operations = operations or getattr(self, 'operations', [])
        self.app = app
        self.name = name
        self.dependencies = dependencies or getattr(self, 'dependencies', [])

    # def apply(self, schema):
    #     for operation in self.operations:
    #         operation.apply(schema)

    # @property
    # def forward_sql(self):
    #     sql, args = zip(*(op.sql for op in self.operations))
    #     return (SQL('\n\n').join(sql), sum(args, ()))

    @dbcursor
    def forward(self, migrations=None, cursor=None):
        if not getattr(self, '_applied', False):
            self._applied = True
            if self.app:
                args = [self.app.name]
            else:
                args = []
            args.append(self.name)
            sql = (
                'SELECT EXISTS('
                '  SELECT 1 FROM polecat_migrations'
                '    WHERE app {}'
                '      AND name = %s'
                ');'
            ).format(
                '= %s' if self.app else 'IS NULL'
            )
            cursor.execute(sql, args)
            result = cursor.fetchone()
            if result[0]:
                return
            migrations = migrations or {}
            for dep_str in self.dependencies:
                dep = migrations[dep_str]
                dep.forward(migrations, cursor=cursor)
            # TODO: This transaction is slightly inefficient.
            with transaction(cursor):
                for op in self.operations:
                    op.forward(cursor=cursor)
                sql = (
                    'INSERT INTO polecat_migrations (app, name, applied)'
                    '  VALUES(%s, %s, now());'
                )
                cursor.execute(sql, (self.app.name if self.app else None, self.name))

    @property
    def filename(self):
        existing_migrations = self.find_existing_migrations()
        if existing_migrations:
            next_number = existing_migrations[-1][0] + 1
        else:
            next_number = 1
        return f'{next_number:04}_migration.py'

    @property
    def migrations_path(self):
        try:
            return self.app.path / 'migrations'
        except AttributeError:
            return project_migrations_path()

    @property
    def dependency_string(self):
        return f'{self.app.name}.{self.filename[:-3]}'

    def set_app(self, app):
        self.app = app
        # TODO: Set app in everywhere else.

    def get_file_path(self, root=None):
        if not root:
            root = self.migrations_path
        else:
            root = Path(root)
        return root / self.filename

    def save(self, output_path=None):
        if not getattr(self, '_saved', False):
            self._saved = True
            file_path = self.get_file_path(output_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(self.serialize())

    def serialize(self):
        dep_strs = []
        for dep in self.dependencies:
            dep.save()
            dep_strs.append(f"'{dep.dependency_string}'")
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
        path = self.migrations_path
        migrations = []
        try:
            for filename in path.iterdir():
                match = self.filename_prog.match(filename.name)
                if match:
                    migrations.append((int(match.group(1)), filename.name))
        except FileNotFoundError:
            pass
        return sorted(migrations, key=lambda x: x[0])
