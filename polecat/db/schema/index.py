from psycopg2.sql import SQL, Identifier


class GistTrigramIndex:
    def __init__(self, column_name):
        self.column_name = column_name

    def bind(self, table):
        self.table = table
        self.name = '{}_{}_trgm_idx'.format(
            self.table.name,
            self.column_name
        )

    @property
    def sql(self):
        return SQL('CREATE INDEX {} ON {} USING GIST ({} gist_trgm_ops)').format(
            Identifier(self.name),
            Identifier(self.table.name),
            Identifier(self.column_name)
        ), ()

    def serialize(self):
        return 'index.GistTrigramIndex(column_name={})'.format(
            repr(self.column_name)
        )
