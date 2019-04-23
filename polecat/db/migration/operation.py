from psycopg2.sql import SQL, Identifier

from ...model.registry import make_role_from_name
from ...utils.predicates import not_empty
from ...utils.stringcase import snakecase
from ..decorators import dbcursor
from .schema import Role, Table

CREATE_ROLE_SQL = '''do $$
  BEGIN
    IF NOT EXISTS(SELECT FROM pg_catalog.pg_roles WHERE rolname = %s) THEN
      CREATE ROLE {};
    END IF;
  END
$$;'''


class Operation:
    def __init__(self):
        pass

    @property
    def dependencies(self):
        return ()

    def apply(self, app, schema):
        pass

    @dbcursor
    def forward(self, cursor):
        cursor.execute(*self.forward_sql)


class CreateExtension(Operation):
    def __init__(self, name):
        super().__init__()
        self.name = name

    @property
    def signature(self):
        return (CreateExtension, self.name)

    @property
    def forward_sql(self):
        return (
            SQL('CREATE EXTENSION IF NOT EXISTS {};').format(
                Identifier(self.name)
            ),
            ()
        )


class CreateTable(Operation):
    def __init__(self, name_or_table, *args, **kwargs):
        super().__init__()
        if not isinstance(name_or_table, Table):
            name_or_table = Table(name_or_table, *args, **kwargs)
        self.table = name_or_table

    # def __repr__(self):
    #     return f'<CreateTable name="{self.name}">'

    @property
    def signature(self):
        return self.table.signature

    @property
    def app(self):
        return self.table.app

    @property
    def dependencies(self):
        for col in self.table.columns.values():
            for dep in col.dependencies:
                yield dep

    # def apply(self, app, schema):
    #     schema.add_model(app, self.name, self.columns, self.options)

    @property
    def sql(self):
        table_name_ident = Identifier(self.get_table_name())
        return (
            SQL('\n').join(
                (SQL('CREATE TABLE {} (\n{}\n);').format(
                    table_name_ident,
                    self.all_sql()
                ),) +
                self.access_sql(table_name_ident)
            ),
            ()
        )

    def all_sql(self):
        return SQL(',\n').join(tuple(filter(not_empty, (
            self.all_columns_sql(),
            self.all_uniques_sql(),
            self.all_checks_sql()
        ))))

    def all_columns_sql(self):
        return SQL(',\n').join(
            SQL('  ') + self.column_sql(f)
            for f in self.iter_valid_columns()
        )

    def all_uniques_sql(self):
        uniques = self.table.options.get('uniques', ())
        if len(uniques):
            return SQL(',\n').join(
                SQL('  UNIQUE ({})').format(self.unique_sql(u))
                for u in uniques
            )
        else:
            None

    def all_checks_sql(self):
        checks = self.table.options.get('checks', ())
        if len(checks):
            return SQL(',\n').join(
                SQL('  CHECK ({})').format(self.check_sql(c))
                for c in checks
            )
        else:
            None

    def iter_valid_columns(self):
        for column in self.table.columns.values():
            yield column

    def column_sql(self, column):
        return column.sql

    def check_sql(self, check):
        if isinstance(check, str):
            return SQL(check)
        raise NotImplemented('checks must be strings')

    def unique_sql(self, unique):
        if isinstance(unique, (tuple, list)):
            return SQL(',').join(map(Identifier, unique))
        raise NotImplemented('uniques must be iterable')

    def access_sql(self, table_name):
        access = getattr(self.table.options, 'access', None)
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
        return self.table.options.get('name', snakecase(self.table.name))


class DeleteTable(Operation):
    pass


class AlterTable(Operation):
    pass


class CreateRole(Operation):
    def __init__(self, name_or_role, *args, **kwargs):
        super().__init__()
        if not isinstance(name_or_role, Role):
            name_or_role = Role(name_or_role, *args, **kwargs)
        self.role = name_or_role

    # def __repr__(self):
    #     return f'<CreateRole name="{self.role.name}">'

    @property
    def signature(self):
        return self.role.signature

    @property
    def app(self):
        return self.role.app

    @property
    def sql(self):
        role_name = self.get_role_name()
        role_name_ident = Identifier(role_name)
        return (
            SQL('\n').join(
                (SQL(CREATE_ROLE_SQL).format(role_name_ident),) +
                self.grants_sql(role_name_ident)
            ),
            (role_name,)
        )

    # def apply(self, app, schema):
    #     schema.add_role(app, self.role.name, self.role.parents)

    def grants_sql(self, role_name):
        return tuple(
            SQL('GRANT {} TO {};').format(
                role_name,
                Identifier(parent)
            )
            for parent in self.role.parents
        )

    def get_role_name(self):
        # TODO: Same operation in models/registry.py.
        return self.role.options.get('role', make_role_from_name(self.role.name))


class DeleteRole(Operation):
    pass


class AlterRole(Operation):
    pass


class RunPython(Operation):
    def __init__(self, forward_func):
        self.forward_func = forward_func

    def foward(self):
        self.forward_func()
