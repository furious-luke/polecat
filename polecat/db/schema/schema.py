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

    def add_role(self, *roles):
        for role in roles:
            self.roles.append(role)
            self.roles_by_name[role.name] = role

    def add_access(self, *accesses):
        for access in accesses:
            self.access.append(access)
            self.access_by_entity[access.entity.signature] = access

    def remove_access(self, *accesses):
        for access in accesses:
            for index, existing in enumerate(self.access):
                if existing.signature == access.signature:
                    self.access.pop(index)
                    del self.access_by_entity[existing.signature]
                    return

    def bind(self):
        for table in self.tables:
            self.bind_table(table)
        for role in self.roles:
            self.bind_role(role)
        for access in self.access:
            self.bind_access(access)

    def bind_table(self, table):
        table.bind(self)

    def bind_role(self, role):
        role.bind(self)

    def bind_access(self, access):
        access.bind(self)

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
