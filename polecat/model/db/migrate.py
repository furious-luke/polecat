from polecat.db.decorators import dbcursor
from polecat.db.migration import diff_schemas, migrate

from .helpers import create_schema


@dbcursor
def sync(migration_paths=None, cursor=None):
    migrate(migration_paths, cursor=cursor)
    # TODO: Build schema from migrations. Should return from above?
    to_schema = create_schema()
    migrations = diff_schemas(to_schema)  # TODO: Add in "from_schema"
    for mgr in migrations:
        mgr.forward()
