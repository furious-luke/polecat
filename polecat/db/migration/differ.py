from .migration import Migration
from .operation import (AlterRole, AlterTable, CreateRole, CreateTable,
                        DeleteRole, DeleteTable)


class Differ:
    def diff(self, from_schema, to_schema):
        self.operations = []
        self.diff_roles(from_schema, to_schema)
        self.diff_tables(from_schema, to_schema)
        self.find_dependencies()
        by_app = {}
        for op in self.operations:
            by_app.setdefault(op.app, []).append(op)
        migrations = {
            app: Migration(ops, app=app)
            for app, ops in by_app.items()
        }
        for mgr in migrations.values():
            dep_mgrs = []
            seen_apps = set()
            for op in mgr.operations:
                for dep in op._dependencies:
                    if dep.app in seen_apps:
                        continue
                    seen_apps.add(dep.app)
                    dep_mgrs.append(migrations[dep.app])
            mgr.dependencies = dep_mgrs
        return list(migrations.values())

    def diff_roles(self, from_schema, to_schema):
        created, deleted, altered = self.diff_entities(from_schema.roles, to_schema.roles)
        self.operations.extend([
            *[
                DeleteRole(role)
                for role in deleted
            ],
            *[
                CreateRole(role)
                for role in created
            ],
            *[
                AlterRole(to_role, from_role)
                for to_role, from_role in altered
            ]
        ])

    def diff_tables(self, from_schema, to_schema):
        created, deleted, altered = self.diff_entities(from_schema.tables, to_schema.tables)
        self.operations.extend([
            *[
                DeleteTable(table)
                for table in deleted
            ],
            *[
                CreateTable(table)
                for table in created
            ],
            *[
                AlterTable(to_table, from_table)
                for to_table, from_table in altered
            ]
        ])

    def find_dependencies(self):
        op_map = {}
        for op in self.operations:
            op_map.setdefault(op.signature, []).append(op)
        for op in self.operations:
            op._dependencies = []
            for dep in op.dependencies:
                # TODO: Oh no... yuck.
                op._dependencies.extend(op_map.get(dep.signature, []))

    def diff_entities(self, from_entities, to_entities):
        from_entities = {
            e.signature: e
            for e in from_entities
        }
        to_entities = {
            e.signature: e
            for e in to_entities
        }
        created = [
            e for e in to_entities.values()
            if e.signature not in from_entities
        ]
        deleted = [
            e for e in from_entities.values()
            if e.signature not in to_entities
        ]
        altered = [
            (e, from_entities[e.signature]) for e in to_entities.values()
            if e.signature in from_entities and from_entities[e.signature] != e
        ]
        # TODO: How to check for renames?
        return (created, deleted, altered)

    def merge_dependencies(self, operations):
        deps = []
        for op in operations:
            for dep in op.dependencies:
                if dep in deps:
                    continue
                deps.append(dep)
        return deps
