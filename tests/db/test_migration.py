from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from polecat.db.migration import (bootstrap_migrations, diff_schemas,
                                  make_migrations, migrate)
from polecat.db.schema import Column, RelatedColumn, Schema, Table

from ..models import schema  # noqa


@pytest.mark.skip(reason='Conflicts between projects and migrations')
def test_migration_from_models(testdb):
    bootstrap_migrations()
    migrations = diff_schemas(schema)
    migrations = [
        *migrations
    ]
    for mgr in migrations:
        # for op in mgr.operations:
        #     sql = testdb.mogrify(*op.sql)
        #     print(sql.decode())
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
    apps = []
    with TemporaryDirectory() as root:
        for mgr in migrations:
            if mgr.app:
                mgr.app.path = Path(root) / mgr.app.name
                apps.append(mgr.app)
        for mgr in migrations:
            mgr.save(root)
        migrate([root], apps=apps)
        # TODO: Test something?


def test_make_migrations(testdb):
    bootstrap_migrations()
    with TemporaryDirectory() as root:
        make_migrations(to_schema=schema, output_path=root)


@pytest.mark.skip(reason='need to rebuild this')
def test_no_new_migrations(testdb):
    bootstrap_migrations()
    with TemporaryDirectory() as root:
        migrations = make_migrations(
            to_schema=schema,
            output_path=root,
            apps=[type('App', (), {
                'name': 'auth',
                'path': Path(root) / 'auth'
            })],
            migration_paths=[root]
        )
        assert len(migrations) != 0
        migrations = make_migrations(
            to_schema=schema,
            output_path=root,
            apps=[type('App', (), {
                'name': 'auth',
                'path': Path(root) / 'auth'
            })],
            migration_paths=[root]
        )
        assert len(migrations) == 0


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
