from tempfile import TemporaryDirectory

import pytest
from polecat.db.migration import bootstrap_migrations, migrate
from polecat.db.migration.operation import CreateExtension
from polecat.db.migration.schema import Column, RelatedColumn, Schema, Table

from .models import AdminRole  # noqa


def test_migration_from_models(testdb):
    bootstrap_migrations()
    schema = Schema.from_models()
    migrations = schema.diff()
    migrations = [
        CreateExtension('chkpass'),
        *migrations
    ]
    for mgr in migrations:
        # sql, args = mgr.forward_sql
        # print(sql.as_string(testdb))
        mgr.forward()


def test_serialize_migration(testdb):
    schema = Schema.from_models()
    migrations = schema.diff()
    for mgr in migrations:
        result = mgr.serialize()
        # TODO: Better test.
        assert result is not None
        assert len(result) > 0


def test_run_migrations(testdb):
    schema = Schema.from_models()
    migrations = schema.diff()
    with TemporaryDirectory() as root:
        migrations[0].operations.insert(0, CreateExtension('chkpass'))
        for mgr in migrations:
            mgr.save(root)
        migrate([root])
        # TODO: Test something?


@pytest.mark.skip(reason='need to mock app registry')
def test_dependencies(testdb):
    bootstrap_migrations()
    schema = Schema(tables=[
        Table('t0', columns=[
            Column('id', 'int', unique=True),
            RelatedColumn('other', 'int', 'a1.t1.id')
        ], app='a0'),
        Table('t1', columns=[
            Column('id', 'int', unique=True)
        ], app='a1')
    ])
    migrations = schema.diff()
    assert len(migrations) == 2
    for mgr in migrations:
        mgr.forward()
