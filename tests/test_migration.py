from tempfile import TemporaryDirectory

import pytest
from polecat.db.migration import bootstrap_migrations, diff_schemas, migrate
from polecat.db.schema import Column, RelatedColumn, Schema, Table

from .models import schema  # noqa


def test_migration_from_models(testdb):
    bootstrap_migrations()
    migrations = diff_schemas(schema)
    migrations = [
        *migrations
    ]
    for mgr in migrations:
        for op in mgr.operations:
            sql = testdb.mogrify(*op.sql)
            print(sql.decode())
        mgr.forward()


def test_serialize_migration(testdb):
    migrations = diff_schemas(schema)
    for mgr in migrations:
        result = mgr.serialize()
        # print(result)
        # TODO: Better test.
        assert result is not None
        assert len(result) > 0


def test_run_migrations(testdb):
    bootstrap_migrations()
    migrations = diff_schemas(schema)
    with TemporaryDirectory() as root:
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
