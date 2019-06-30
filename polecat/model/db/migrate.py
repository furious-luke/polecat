from polecat.core.context import active_context
from polecat.db.decorators import dbcursor
from polecat.db.migration import diff_schemas
from polecat.db.migration import make_migrations as db_make_migrations
from polecat.db.migration import migrate

from .helpers import create_schema


@dbcursor
def sync(migration_paths=None, cursor=None):
    migrate(migration_paths, cursor=cursor)
    # TODO: Build schema from migrations. Should return from above?
    to_schema = create_schema()
    migrations = diff_schemas(to_schema)  # TODO: Add in "from_schema"
    for mgr in migrations:
        mgr.forward()


@active_context
def make_migrations(context=None, **kwargs):
    return db_make_migrations(
        apps=context.registries.app_registry,
        **kwargs
    )
