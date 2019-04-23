from psycopg2.sql import SQL, Identifier

from ...model.field import MutableField, RelatedField
from ...model.registry import model_registry, role_registry
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
        return cls(tables, roles)

    def __init__(self, tables=None, roles=None):
        self.tables = tables or []
        self.roles = roles or []

    def diff(self, from_schema=None):
        if from_schema is None:
            from_schema = Schema()
        return self.get_differ().diff(from_schema, self)

    def apply(self, migration):
        migration.apply(self)

    def forward(self, operation):
        pass

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


class Table:
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

    def __eq__(self, other):
        return (
            self.app == other.app and
            self.name == other.name and
            self.options == other.options and
            self.columns == other.columns
        )

    @property
    def signature(self):
        return (Table, self.app, self.name)


class Column:
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

    def __eq__(self, other):
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


class RelatedColumn(Column):
    def __init__(self, name, type, references, *args, **kwargs):
        super().__init__(name, type, *args, **kwargs)
        self.references = references

    def __repr__(self):
        return f'<RelatedColumn name="{self.name}" references="{self.references}">'

    def __eq__(self, other):
        return (
            super().__eq__(other) and
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


class Role:
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

    def __eq__(self, other):
        return (
            self.app == other.app and
            self.name == other.name and
            self.parents == other.parents
        )

    @property
    def signature(self):
        return (Role, self.app, self.name)
