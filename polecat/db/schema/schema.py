__all__ = ('Schema',)


class Schema:
    def __init__(self, tables=None, roles=None, access=None):
        self.tables = tables or []
        self.tables_by_name = {
            t.name: t
            for t in self.tables
        }
        self.roles = roles or []
        self.roles_by_name = {
            r.name: r
            for r in self.roles
        }
        self.access = access or []
        self.access_by_entity = {
            a.entity.signature: a
            for a in self.access
        }

    def add_table(self, *tables):
        for table in tables:
            self.tables.append(table)
            self.tables_by_name[table.name] = table

    def bind(self):
        for table in self.tables:
            table.bind(self)

    def get_table_by_name(self, name):
        return self.tables_by_name[name]

    def get_role_by_name(self, name):
        return self.roles_by_name[name]

    def get_access_by_entity(self, entity):
        return self.access_by_entity[entity.signature]

    def merge_access(self):
        all_access = {}
        for access in self.access:
            all_access[access.signature] = access
        return tuple(all_access.values())
