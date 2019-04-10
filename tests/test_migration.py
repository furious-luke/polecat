from polecat.db.migration import from_models

from .models import *  # noqa


def test_migration_sql_from_models(testdb):
    migration = from_models()
    sql, args = migration.forward_sql()
    # print(sql.as_string(testdb))
