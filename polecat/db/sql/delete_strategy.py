from polecat.db.query import query as query_module

from .expression.delete import Delete
from .expression.where import Where
from .expression.subquery import Subquery


class DeleteStrategy:
    def __init__(self, root_strategy):
        self.root = root_strategy

    def parse_query(self, query):
        if isinstance(query.source, query_module.Filter):
            relation = query.source.source
            # TODO: This doesn't belong here.
            options = {}
            for k, v in query.source.options.items():
                if isinstance(v, query_module.Select):
                    v = Subquery(
                        self.root.create_select(v)
                    )
                options[k] = v
            where = Where(**options)
        else:
            relation = query.source
            where = None
        return Delete(relation, where=where)
