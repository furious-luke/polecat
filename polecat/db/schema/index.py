from psycopg2.sql import SQL, Identifier


class Index:
    def __init__(self, column_name):
        self.column_name = column_name

    def bind(self, table):
        self.table = table
        self.name = '{}_{}_{}'.format(
            self.table.name,
            self.column_name,
            self._get_suffix()
        )

    @property
    def sql(self):
        return SQL('CREATE INDEX {} ON {} ({})').format(
            Identifier(self.name),
            Identifier(self.table.name),
            Identifier(self.column_name)
        ), ()

    def serialize(self):
        return 'index.Index(column_name={})'.format(
            repr(self.column_name)
        )

    def _get_suffix(self):
        return 'idx'


class GistTrigramIndex(Index):
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

    def _get_suffix(self):
        return 'trgm_idx'
