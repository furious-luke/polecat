import re
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from polecat.db.schema import Schema

from ...utils import indent
from ..connection import transaction
from ..decorators import dbcursor
from .utils import project_migrations_path

migration_template = '''from polecat.db.migration import migration, operation
from polecat.db import schema
from polecat.db.schema import column


class Migration(migration.Migration):
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

    def __init__(self, operations=None, app=None, dependencies=None, name=None, filename=None):
        self.operations = operations or getattr(self, 'operations', [])
        self.app = app
        self.name = name
        self.dependencies = dependencies or getattr(self, 'dependencies', [])
        self._filename = filename

    @dbcursor
    def forward(self, schema=None, migrations=None, schema_only=False, cursor=None):
        # TODO: This "_applied" thing means we can only run this
        # once. Probably need to improve that.
        if not getattr(self, '_applied', False):
            self._applied = True
            if not schema:
                schema = Schema()
            if not schema_only:
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
                is_applied = cursor.fetchone()[0]
            else:
                is_applied = False
            migrations = migrations or {}
            for dep in self.dependencies:
                if isinstance(dep, str):
                    dep = migrations[dep]
                dep.forward(schema, migrations, cursor=cursor)
            # TODO: This transaction is slightly inefficient.
            with transaction(cursor):
                for op in self.operations:
                    op.forward_schema(schema)
                    if not is_applied and not schema_only:
                        op.forward(schema, cursor=cursor)
                if not is_applied and not schema_only:
                    sql = (
                        'INSERT INTO polecat_migrations (app, name, applied)'
                        '  VALUES(%s, %s, now());'
                    )
                    cursor.execute(sql, (self.app.name if self.app else None, self.name))

    @property
    def filename(self):
        if not self._filename:
            existing_migrations = self.find_existing_migrations()
            if existing_migrations:
                next_number = existing_migrations[-1][0] + 1
            else:
                next_number = 1
            self._filename = f'{next_number:04}_migration.py'
        return self._filename

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
        for op in self.operations:
            op.set_app(app)

    def get_file_path(self, root=None):
        if not root:
            root = self.migrations_path
        else:
            root = Path(root)
            if self.app:
                root /= self.app.name
            root /= 'migrations'
        return root / self.filename

    def save(self, output_path=None):
        if not getattr(self, '_saved', False):
            self._saved = True
            file_path = self.get_file_path(output_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(self.serialize())
            file_path = Path(file_path).parent / '__init__.py'
            if not file_path.exists():
                file_path.touch()

    def serialize(self):
        dep_strs = []
        for dep in self.dependencies:
            # dep.save()
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
