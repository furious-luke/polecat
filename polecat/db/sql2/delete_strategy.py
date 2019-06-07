from .expression.delete import Delete


class DeleteStrategy:
    def __init__(self, root_strategy):
        self.root = root_strategy

    def parse_query(self, query):
        return Delete(query.source)
