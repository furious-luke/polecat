from psycopg2.sql import SQL, Identifier

from ...model.field import MutableField, RelatedField
from ...model.model import Model
from ...model.registry import access_registry, model_registry, role_registry
from ...utils.stringcase import snakecase
from ..field import get_db_field


class Schema:
    differ_class = None

    @classmethod
    def from_models(cls):
        tables = [
            Table.from_model(model)
            for model in model_registry
        ]
        roles = [
            Role.from_model_role(role)
            for role in role_registry
        ]
        access = [
            Access.from_model_access(access)
            for access in access_registry
        ]
        return cls(tables, roles, access)

    def __init__(self, tables=None, roles=None, access=None):
        self.tables = tables or []
        self.roles = roles or []
        self.access = access or []

    def diff(self, from_schema=None):
        if from_schema is None:
            from_schema = Schema()
        return self.get_differ().diff(from_schema, self)

    def apply(self, migration):
        migration.apply(self)

    def forward(self, operation):
        pass

    def merge_access(self):
        all_access = {}
        for access in self.access:
            all_access[access.signature] = access
        return tuple(all_access.values())

    def add_table(self, table):
        # TODO: Validate.
        self.tables.append(table)

    def add_role(self, role):
        # TODO: Validate.
        self.roles.append(role)

    def get_differ(self):
        # TODO: Is this a problem?
        from .differ import Differ
        return (self.differ_class or Differ)()


class Entity:
    def __eq__(self, other):
        return self.signature == other.signature


class Table(Entity):
    tag = 'TABLE'

    @classmethod
    def from_model(cls, model):
        columns = []
        for field in model.Meta.fields.values():
            if not isinstance(field, MutableField):
                continue
            col = Column.from_model_field(field)
            columns.append(col)
        app = model.Meta.app
        app_name = app.name if app else None
        return cls(model.Meta.name, columns, model.Meta.options, app=app_name)

    def __init__(self, name, columns=None, options=None, app=None):
        self.app = app
        self.name = name
        # TODO: Validate columns.
        self.columns = columns or []
        self.options = options or {}

    def __hash__(self):
        return hash(self.signature)

    @property
    def signature(self):
        return (Table, self.app, self.name)

    @property
    def dbname(self):
        return self.options.get('name', snakecase(self.name))

    def has_changed(self, other):
        return (
            self.app == other.app and
            self.name == other.name and
            self.options == other.options and
            self.columns == other.columns
        )

    def serialize(self):
        return f"Table('{self.name}')"


class Column(Entity):
    @classmethod
    def from_model_field(cls, field):
        db_field = get_db_field(field)
        args = []
        kwargs = {
            'primary_key': db_field.primary_key,
            'unique': db_field.unique,
            'null': db_field.null
        }
        if isinstance(field, RelatedField):
            cls = RelatedColumn
            args.append(db_field.references)
        return cls(db_field.name, db_field.type, *args, **kwargs)

    def __init__(self, name, type, unique=False, null=True, primary_key=False):
        self.name = name
        self.type = type
        self.unique = unique
        self.null = null
        self.primary_key = primary_key

    def __repr__(self):
        return f'<Column name="{self.name}" type="{self.type}">'

    def __hash__(self):
        return hash(self.signature)

    def has_changed(self, other):
        return (
            self.__class__ == other.__class__ and
            self.name == other.name and
            self.type == other.type
        )

    @property
    def signature(self):
        return (Column, self.name,)

    @property
    def dependencies(self):
        return ()

    @property
    def sql(self):
        parts = ['{}', self.type]
        parts.extend(self.constraints)
        return SQL(' '.join(parts)).format(
            Identifier(self.name)
        )

    @property
    def constraints(self):
        constraints = []
        if self.primary_key:
            constraints.append('PRIMARY KEY')
        else:
            if not self.null:
                constraints.append('NOT NULL')
            if self.unique:
                constraints.append('UNIQUE')
        return constraints

    def serialize(self):
        cls = self.serialize_class()
        type = self.serialize_type()
        args = self.serialize_args()
        if args:
            args = f', {args}'
        return f"{cls}('{self.name}', '{type}'{args})"

    def serialize_class(self):
        return self.__class__.__name__

    def serialize_type(self):
        return self.type

    def serialize_args(self):
        args = []
        if not self.null:
            args.append('null=False')
        if self.unique:
            args.append('unique=True')
        if self.primary_key:
            args.append('primary_key=True')
        return ', '.join(args) or ''


class RelatedColumn(Column):
    def __init__(self, name, type, references, *args, **kwargs):
        super().__init__(name, type, *args, **kwargs)
        self.references = references

    def __repr__(self):
        return f'<RelatedColumn name="{self.name}" references="{self.references}">'

    def __hash__(self):
        return hash(self.signature)

    def has_changed(self, other):
        return (
            super().has_changed(other) and
            self.references == other.references
        )

    @property
    def dependencies(self):
        app, table, field = self.split_reference()
        return (Table(table, app=app),)

    @property
    def sql(self):
        return SQL('{} %s {}' % self.type).format(
            Identifier(self.name),
            self.reference_sql
        )

    @property
    def reference_sql(self):
        app, table, field = self.split_reference()
        return SQL('REFERENCES {}({})').format(
            Identifier(table),
            Identifier(field)
        )

    def split_reference(self):
        parts = self.references.split('.')
        if len(parts) == 2:
            app = None
            table = parts[0]
            field = parts[1]
        else:
            app = parts[0]
            table = parts[1]
            field = parts[2]
        return (app, table, field)

    def serialize_args(self):
        args = super().serialize_args()
        if args:
            args += ', '
        args += f"'{self.references}'"
        return args


class Role(Entity):
    tag = 'ROLE'

    @classmethod
    def from_model_role(cls, role):
        parents = [
            parent.Meta.role
            for parent in role.parents
        ]
        app = role.Meta.app
        app_name = app.name if app else None
        return cls(role.Meta.role, parents, app=app_name)

    def __init__(self, name, parents=None, options=None, app=None):
        self.app = app
        self.name = name
        self.parents = set(parents or ())
        self.options = options or {}

    def __hash__(self):
        return hash(self.signature)

    def has_changed(self, other):
        return (
            # self.app == other.app and
            self.name == other.name and
            self.parents == other.parents
        )

    @property
    def signature(self):
        # TODO: I've removed `sel.app` from the signature for now,
        # meaning roles are across apps.
        return (Role, self.name)

    def serialize(self, operation=None):
        if not operation:
            operation = 'Role'
        parents = self.serialize_parents()
        if parents:
            parents = f', parents={parents}'
        return f"{operation}('{self.name}'{parents})"

    def serialize_parents(self):
        parents = '[' + ', '.join(f"'{p}'" for p in self.parents) + ']'
        return parents


class Access(Entity):
    @classmethod
    def from_model_access(cls, access):
        entity = access.entity
        if issubclass(entity, Model):
            entity = Table.from_model(entity)
        else:
            raise NotImplementedError
        # TODO: Hmm, this is a bit ugly.
        return cls(
            entity,
            all=[Role(a.Meta.role, app=a.app) for a in access.all],
            select=[Role(a.Meta.role, app=a.app) for a in access.select],
            insert=[Role(a.Meta.role, app=a.app) for a in access.insert],
            update=[Role(a.Meta.role, app=a.app) for a in access.update],
            delete=[Role(a.Meta.role, app=a.app) for a in access.delete],
            app=getattr(access, 'app', None)
        )

    def __init__(self, entity, all=None, select=None, insert=None, update=None,
                 delete=None, app=None):
        self.entity = entity
        self.all = all
        self.select = select
        self.insert = insert
        self.update = update
        self.delete = delete
        self.app = app

    def __hash__(self):
        return hash(self.signature)

    def has_changed(self, other):
        return (
            self.entity != other.entity and
            self.all == other.all and
            self.select == other.select and
            self.insert == other.insert and
            self.update == other.update and
            self.delete == other.delete
        )

    @property
    def signature(self):
        return (Access, self.entity.signature)
