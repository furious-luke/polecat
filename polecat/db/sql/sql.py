from ...utils import to_class
from .query import Query


# TODO: Should probably just use query.Query?
class Q:
    def __init__(self, model):
        self.model_class = to_class(model)
        self.model = model

    def select(self, *fields, **lookups):
        return Query(self.model_class).select(*fields, **lookups)

    def get(self, *args, **kwargs):
        return Query(self.model_class).get(*args, **kwargs)

    def insert(self, *fields, **lookups):
        return Query(self.model).insert(*fields, **lookups)

    def delete(self):
        return Query(self.model).delete()
