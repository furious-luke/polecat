# from polecat.db.migration import from_models
from polecat.db.migration.operation import CreateExtension
from polecat.db.migration.schema import Column, RelatedColumn, Schema, Table

from .models import *  # noqa


def test_migration_from_models(testdb):
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


def test_dependencies(testdb):
    schema = Schema(tables=[
        Table('t0', columns={
            'id': Column('id', 'int', unique=True),
            'other': RelatedColumn('other', 'int', 'a1.t1.id')
        }, app='a0'),
        Table('t1', columns={
            'id': Column('id', 'int', unique=True)
        }, app='a1')
    ])
    migrations = schema.diff()
    assert len(migrations) == 2
    for mgr in migrations:
        mgr.forward()
