from stdb.core.engine import default_engine as engine

from .query import Query


class Delete(Query):
    def __init__(self, version, endpoint, id, **kwargs):
        super().__init__(version, endpoint, **kwargs)
        self.id = id

    def execute(self):
        sql = self.get_sql()
        engine.execute(sql)

    def get_sql(self):
        return (
            'DELETE FROM {} WHERE id = {};'
        ).format(
            self.endpoint['table'],
            engine.quote_literal(self.id)
        )
