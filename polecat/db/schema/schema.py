__all__ = ('Schema',)


class Schema:
    def __init__(self):
        self.tables = []
        self.tables_by_name = {}

    def add_table(self, *tables):
        for table in tables:
            self.tables.append(table)
            self.tables_by_name[table.name] = table

    def bind(self):
        for table in self.tables:
            table.bind(self)

    def get_table_by_name(self, name):
        return self.tables_by_name[name]
