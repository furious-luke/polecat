from polecat.db.query import query as query_module

from .expression.delete import Delete
from .expression.where import Where


class DeleteStrategy:
    def __init__(self, root_strategy):
        self.root = root_strategy

    def parse_query(self, query):
        if isinstance(query.source, query_module.Filter):
            relation = query.source.source
            where = Where(**query.source.options)
        else:
            relation = query.source
            where = None
        return Delete(relation, where=where)
