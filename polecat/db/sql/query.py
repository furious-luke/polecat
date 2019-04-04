from ...utils import to_class
from ..connection import cursor
from .filter import Filter
from .lateral import LateralBackend
from .lookup import Lookup
from .selector import Selector


class Query:
    backend_class = LateralBackend
    lookup_class = Lookup

    def __init__(self, model, selector=None, parent=None, filter=None):
        self.model_class = to_class(model)
        self.selector = selector
        self.parent = parent
        self.filter = filter
        self.id = parent.next_id if parent else 0
        self.next_id = self.id + 1
        self.table_alias = f't{self.id}'
        self.join_alias = f'j{self.id}'

    def __repr__(self):
        return f'<Query selector={self.selector}>'

    def __getitem__(self, key):
        result = self.execute()
        if getattr(self, 'is_get', False):
            return result[0][key]
        else:
            return result[key]

    def select(self, *fields, **lookups):
        if len(fields) == 1 and isinstance(fields[0], Selector):
            self.selector = fields[0]
        else:
            self.selector = Selector(*fields, **lookups)
        return self

    def get(self, **lookups):
        self.filter = Filter(lookups)
        self.is_get = True
        return self

    def execute(self):
        result = getattr(self, '_result', None)
        if not result:
            # TODO: Don't reconnect everytime, dufus.
            with cursor() as curs:
                curs.execute(*self.evaluate())
                result = tuple(map(lambda x: x[0], curs.fetchall()))
                self._result = result
        return result

    def evaluate(self):
        self.prepare()
        sql = getattr(self, '_sql', None)
        if sql is None:
            sql = self.backend_class.evaluate(self)
            self._sql = sql
        return sql

    def prepare(self):
        if not getattr(self, '_prepared', False):
            self.fields = self.selector.fields
            self.prepare_lookups()
            self._prepared = True
        return self

    def prepare_lookups(self):
        self.lookups = {
            field_name: self.prepare_sub_query(field_name, selector)
            for field_name, selector in self.selector.lookups.items()
        }

    def prepare_sub_query(self, field_name, selector):
        # TODO: Handle invalid lookup.
        other_model = self.model_class.Meta.fields[field_name].other
        sub_query = Query(other_model, selector=selector, parent=self).prepare()
        self.next_id = sub_query.next_id
        return sub_query
