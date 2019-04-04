from .filter import Filter
from .multi.list import List


class Detail(List):
    def __init__(self, version, endpoint, id, include=[], where=[], **kwargs):
        self.id = id
        table = endpoint['table']
        flt = Filter({'id': id})
        super().__init__(version, endpoint, include, filter=flt, limit=1, **kwargs)
