from psycopg2.sql import SQL, Identifier

from ...model.registry import make_role_from_name
from ...utils.stringcase import snakecase
from ..field import get_db_field

CREATE_ROLE_SQL = '''do $$
  BEGIN
    IF NOT EXISTS(SELECT FROM pg_catalog.pg_roles WHERE rolname = %s) THEN
      CREATE ROLE {};
    END IF;
  END
$$;'''


class Operation:
    def __init__(self, options=None):
        self.options = options or {}


class CreateExtension(Operation):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def forward_sql(self):
        return (
            SQL('CREATE EXTENSION IF NOT EXISTS {};').format(
                Identifier(self.name)
            ),
            ()
        )


class CreateModel(Operation):
    def __init__(self, name, fields, options=None):
        super().__init__(options)
        self.name = name
        self.fields = fields
        self.options = options or {}

    def __repr__(self):
        return f'<CreateModel name="{self.name}">'

    def forward_sql(self):
        table_name_ident = Identifier(self.get_table_name())
        return (
            SQL('\n').join(
                (SQL('CREATE TABLE {} ({});').format(
                    table_name_ident,
                    self.all_fields_sql()
                ),) +
                self.access_sql(table_name_ident)
            ),
            ()
        )

    def all_fields_sql(self):
        return SQL('\n{}\n').format(
            SQL(',\n').join(
                SQL('  ') + self.field_sql(f)
                for f in self.fields
            )
        )

    def field_sql(self, field):
        return get_db_field(field).get_create_sql()

    def access_sql(self, table_name):
        access = getattr(self.options, 'access', None)
        if access:
            grants = tuple(self.iter_grants(access, table_name))
        else:
            grants = ()
        return grants

    def iter_grants(self, access, table_name):
        roles_and_perms = (
            (access.all, 'ALL'),
            (access.select, 'SELECT'),
            (access.insert, 'INSERT'),
            (access.update, 'UPDATE'),
            (access.delete, 'DELETE')
        )
        for roles, perm in roles_and_perms:
            if roles:
                for role in roles:
                    yield SQL('GRANT %s ON {} TO {};' % perm).format(
                        table_name,
                        Identifier(role.Meta.role)
                    )

    def get_table_name(self):
        # TODO: Same operation in models/registry.py.
        return getattr(self.options, 'name', snakecase(self.name))


class CreateRole(Operation):
    def __init__(self, name, parents=None, options=None):
        super().__init__(options)
        self.name = name
        self.parents = parents or ()

    def __repr__(self):
        return f'<CreateRole name="{self.name}">'

    def forward_sql(self):
        role_name = self.get_role_name()
        role_name_ident = Identifier(role_name)
        return (
            SQL('\n').join(
                (SQL(CREATE_ROLE_SQL).format(role_name_ident),) +
                self.grants_sql(role_name_ident)
            ),
            (role_name,)
        )

    def grants_sql(self, role_name):
        return tuple(
            SQL('GRANT {} TO {};').format(
                role_name,
                Identifier(parent.Meta.role)
            )
            for parent in self.parents
        )

    def get_role_name(self):
        # TODO: Same operation in models/registry.py.
        return getattr(self.options, 'role', make_role_from_name(self.name))
