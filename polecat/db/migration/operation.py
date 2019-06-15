from psycopg2.sql import SQL, Identifier

from ...core.context import active_context
from ...model.registry import make_role_from_name
from ...utils import indent
from ...utils.predicates import not_empty
from ..decorators import dbcursor
from ..schema import Access, MutableColumn, Role, Table
from .column import Column  # noqa

create_role_sql = '''do $$
  BEGIN
    IF NOT EXISTS(SELECT FROM pg_catalog.pg_roles WHERE rolname = %s) THEN
      CREATE ROLE {};
    END IF;
  END
$$;'''

create_table_template = '''operation.CreateTable(
    '{}',
    columns=[{}]{}
)'''


class Operation:
    def __init__(self):
        pass

    @property
    def dependencies(self):
        return ()

    @dbcursor
    def forward(self, cursor):
        cursor.execute(*self.sql)


class CreateExtension(Operation):
    def __init__(self, name):
        super().__init__()
        self.name = name

    @property
    def signature(self):
        return (CreateExtension, self.name)

    @property
    def sql(self):
        return (
            SQL('CREATE EXTENSION IF NOT EXISTS {};').format(
                Identifier(self.name)
            ),
            ()
        )

    def serialize(self):
        return f"CreateExtension('{self.name}')"


class CreateTable(Operation):
    def __init__(self, name_or_table, *args, **kwargs):
        super().__init__()
        if not isinstance(name_or_table, Table):
            name_or_table = Table(name_or_table, *args, **kwargs)
        self.table = name_or_table

    @property
    def signature(self):
        return self.table.signature

    @property
    def app(self):
        return self.table.app

    @property
    def dependencies(self):
        for col in self.table.columns:
            for dep in col.dependencies:
                yield dep

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
            SQL('  ') + self.column_sql(column)
            for column in self.iter_valid_columns()
        )

    def all_uniques_sql(self):
        uniques = self.table.uniques
        if len(uniques):
            return SQL(',\n').join(
                SQL('  UNIQUE ({})').format(self.unique_sql(u))
                for u in uniques
            )
        else:
            None

    def all_checks_sql(self):
        checks = self.table.checks
        if len(checks):
            return SQL(',\n').join(
                SQL('  CHECK ({})').format(self.check_sql(c))
                for c in checks
            )
        else:
            None

    @active_context
    def iter_valid_columns(self, context):
        registry = context.registries.migration_column_registry
        for column in self.table.columns:
            if isinstance(column, MutableColumn):
                yield registry[column](column)

    def column_sql(self, column):
        return column.to_sql()

    def check_sql(self, check):
        if isinstance(check, str):
            return SQL(check)
        raise NotImplemented('checks must be strings')

    def unique_sql(self, unique):
        if isinstance(unique, (tuple, list)):
            return SQL(',').join(map(Identifier, unique))
        raise NotImplemented('uniques must be iterable')

    def access_sql(self, table_name):
        access = self.table.access
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
        # TODO: Also, not sure this should even exist... should I be
        # just setting the actual table name instead of the model
        # name?
        return self.table.name

    def serialize(self):
        columns = self.serialize_valid_columns()
        if columns:
            columns = indent(f'\n{columns}', 8)
            columns += indent('\n')
        options = []
        access = self.serialize_access()
        if access:
            options.append(f'access={access}')
        checks = self.serialize_checks()
        if checks:
            options.append(f'checks={checks}')
        uniques = self.serialize_uniques()
        if uniques:
            options.append(f'uniques={uniques}')
        options = ',\n'.join(options)
        if options:
            options = indent(f',\n{options}', 4)
        return create_table_template.format(
            self.table.name,
            columns,
            options
        )

    def serialize_valid_columns(self):
        cols = []
        for col in self.iter_valid_columns():
            cols.append(self.serialize_column(col.schema_column))
        return ',\n'.join(cols)

    def serialize_column(self, column):
        cargs = column.get_construction_arguments()
        return f'column.{column.__class__.__name__}({str(cargs)})'

    def serialize_access(self):
        access = self.table.access
        if access:
            access = {
                'all': [a.Meta.role for a in access.all],
                'select': [a.Meta.role for a in access.select],
                'insert': [a.Meta.role for a in access.insert],
                'update': [a.Meta.role for a in access.update],
                'delete': [a.Meta.role for a in access.delete]
            }
            access = {
                k: v
                for k, v in access.items()
                if len(v) > 0
            }
            # TODO: Maybe try make it indented and pretty?
            access = str(access)
        return access

    def serialize_checks(self):
        checks = self.table.checks
        if checks:
            checks = str(checks)
        return checks

    def serialize_uniques(self):
        uniques = self.table.uniques
        if uniques:
            uniques = str(uniques)
        return uniques


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

    @property
    def dependencies(self):
        return self.role.parents

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
                (SQL(create_role_sql).format(role_name_ident),) +
                self.grants_sql(role_name_ident)
            ),
            (role_name,)
        )

    def grants_sql(self, role_name):
        return tuple(
            SQL('GRANT {} TO {};').format(
                role_name,
                Identifier(getattr(parent, 'name', parent))
            )
            for parent in self.role.parents
        )

    def get_role_name(self):
        # TODO: Same operation in models/registry.py.
        return self.role.options.get('role', make_role_from_name(self.role.name))

    def serialize(self):
        parents = self.serialize_role_parents(self.role)
        if parents:
            parents = f', parents={parents}'
        return f"operation.CreateRole('{self.role.name}'{parents})"

    def serialize_role_parents(self, role):
        parents = '[' + ', '.join(f"'{p.name}'" for p in role.parents) + ']'
        return parents


class DeleteRole(Operation):
    pass


class AlterRole(Operation):
    pass


class GrantAccess(Operation):
    def __init__(self, entity_or_access, *args, **kwargs):
        super().__init__()
        if not isinstance(entity_or_access, Access):
            entity_or_access = Access(entity_or_access, *args, **kwargs)
        self.access = entity_or_access

    @property
    def signature(self):
        return (GrantAccess, self.access.signature)

    @property
    def app(self):
        return self.access.app

    @property
    def sql(self):
        # TODO: Awful.
        access_sql = filter(not_empty, [
            self.get_access_sql(access, roles)
            for access, roles in [
                ('SELECT', set(map(lambda r: getattr(r, 'name', r), self.access.all)) | set(map(lambda r: getattr(r, 'name', r), self.access.select))),
                ('INSERT', set(map(lambda r: getattr(r, 'name', r), self.access.all)) | set(map(lambda r: getattr(r, 'name', r), self.access.insert))),
                ('UPDATE', set(map(lambda r: getattr(r, 'name', r), self.access.all)) | set(map(lambda r: getattr(r, 'name', r), self.access.update))),
                ('DELETE', set(map(lambda r: getattr(r, 'name', r), self.access.all)) | set(map(lambda r: getattr(r, 'name', r), self.access.delete))),
            ]
        ])
        return SQL('\n').join(access_sql), ()

    @property
    def entity_sql(self):
        tag = self.get_entity_tag(self.access.entity)
        return SQL('%s {}' % tag).format(
            Identifier(self.access.entity if isinstance(self.access.entity, str) else self.access.entity.name)
        )

    def get_entity_tag(self, entity):
        raise NotImplementedError

    def get_access_sql(self, access, roles):
        if not roles:
            return None
        return SQL('GRANT %s ON {} TO {};' % access).format(
            self.entity_sql,
            SQL(', ').join([
                Identifier(r if isinstance(r, str) else r.name)  # TODO: Explain
                for r in roles
            ])
        )

    def serialize(self):
        # TODO: Fix this.
        entity = self.serialize_entity()
        access = [
            ('all', [r.name for r in self.access.all]),
            ('select', [r.name for r in self.access.select]),
            ('insert', [r.name for r in self.access.insert]),
            ('update', [r.name for r in self.access.update]),
            ('delete', [r.name for r in self.access.delete])
        ]
        access = ', '.join([f'{a[0]}={a[1]}' for a in access if len(a[1])])
        return f'operation.{self.__class__.__name__}({repr(entity)}, {access})'

    def serialize_entity(self):
        entity = self.access.entity
        if isinstance(entity, str):
            entity_string = entity
        else:
            entity_string = self.entity.name
        return entity_string


class GrantAccessToTable(GrantAccess):
    def serialize_entity(self):
        entity = self.access.entity
        if isinstance(entity, str):
            entity_string = entity
        else:
            entity_string = entity.name
            if entity.app:
                entity_string = f'{entity.app}.{entity_string}'
        return entity_string

    def get_entity_tag(self, entity):
        return 'TABLE'


class GrantAccessToRole(GrantAccess):
    def get_entity_tag(self, entity):
        return 'ROLE'


class RevokeAccess(Operation):
    def __init__(self, entity_or_access, *args, **kwargs):
        super().__init__()
        if not isinstance(entity_or_access, Access):
            entity_or_access = Access(entity_or_access, *args, **kwargs)
        self.access = entity_or_access

    @property
    def signature(self):
        return (RevokeAccess, self.access.signature)

    @property
    def app(self):
        return self.access.app


class RunPython(Operation):
    def __init__(self, forward_func):
        self.forward_func = forward_func

    @dbcursor
    def forward(self, cursor):
        self.forward_func(cursor)
