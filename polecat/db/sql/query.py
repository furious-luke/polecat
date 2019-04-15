from psycopg2.sql import SQL, Identifier, Placeholder

from ...project import configuration
from ...utils import to_class
from ..connection import cursor
from .delete import Delete
from .filter import Filter
from .insert import Insert
from .lateral import LateralBackend
from .lookup import Lookup
from .selector import Selector


class Query:
    # TODO: Rename to select class?
    backend_class = LateralBackend
    lookup_class = Lookup
    insert_class = Insert
    delete_class = Delete

    def __init__(self, model, selector=None, parent=None, filter=None):
        self.model = model
        self.model_class = to_class(model)
        self.selector = selector
        self.parent = parent
        self.filter = filter
        self.id = parent.next_id if parent else 0
        self.next_id = self.id + 1
        self.table_alias = f't{self.id}'
        self.join_alias = f'j{self.id}'
        self.agg_alias = f'a{self.id}'
        self.is_get = False
        self.is_select = False
        self.is_insert = False
        self.is_delete = False

    def __repr__(self):
        return f'<Query selector={self.selector}>'

    def __getitem__(self, key):
        result = self.execute()
        return result[key]

    def select(self, *fields, **lookups):
        self.is_select = True
        if len(fields) == 1 and isinstance(fields[0], Selector):
            self.selector = fields[0]
        else:
            self.selector = Selector(*fields, **lookups)
        # if self.is_insert:
        #     # TODO: Check for pre-existing get?
        #     # TODO: Combine with `insert` method?
        #     self.get(id=SQL('{}.{}').format(
        #         Identifier('cte0'),
        #         Identifier('id')
        #     ))
        return self

    def get(self, **filters):
        """ Get applies filters and sets the query to return a single
        object.
        """
        self.is_get = True
        self.filter = Filter(filters)
        return self

    def insert(self, *fields, **lookups):
        # TODO: Must have a full model instance.
        self.is_insert = True
        # TODO: How to handle non-id PKs?
        # TODO: How to handle unpredictable cte aliases?
        # if self.is_select:
        #     # TODO: Check for pre-existing get?
        #     # TODO: Combine with `select` method?
        #     self.get(id=SQL('{}.{}').format(
        #         Identifier('cte0'),
        #         Identifier('id')
        #     ))
        return self

    def delete(self):
        self.is_delete = True
        return self

    def execute(self):
        result = getattr(self, '_result', None)
        if not result:
            # TODO: Don't reconnect everytime, dufus.
            with cursor() as curs:
                if self.is_insert:
                    insert_sql, select_sql = self.evaluate()
                    if configuration.log_sql:
                        print(curs.mogrify(insert_sql[0], insert_sql[1]))
                    curs.execute(*insert_sql)
                    id = curs.fetchone()[0]
                    if configuration.log_sql:
                        print(curs.mogrify(select_sql[0], (id,)))
                    curs.execute(select_sql[0], (id,))
                    result = tuple(map(lambda x: x[0], curs.fetchall()))
                    self.update_model(result)
                else:
                    sql, args = self.evaluate()
                    if configuration.log_sql:
                        print(curs.mogrify(sql, args))
                    curs.execute(sql, args)
                    if not self.is_delete:
                        result = tuple(map(lambda x: x[0], curs.fetchall()))
                # TODO: Move this above `update_model`.
                if self.is_get:
                    if result:
                        result = result[0]
                    else:
                        # TODO: Throw error?
                        result = None
                self._result = result
        return result

    def evaluate(self, *args, **kwargs):
        self.prepare()
        sql = getattr(self, '_sql', None)
        if sql is None:
            if self.is_delete:
                sql = self.delete_class.evaluate(self.model)
            elif self.is_insert:
                insert_cte = self.insert_class.evaluate(self.model, self.selector)  # TODO: Need *args, **kwargs?
                insert_sql = insert_cte.evaluate()
                select_sql = self.backend_class.evaluate(self, *args, **kwargs)
                sql = (
                    (
                        SQL('WITH {} SELECT id FROM {}').format(
                            insert_sql[0],
                            Identifier(insert_cte.alias)
                        ),
                        insert_sql[1]
                    ),
                    select_sql
                )
            else:
                sql = self.backend_class.evaluate(self, *args, **kwargs)
            self._sql = sql
        return sql

    def prepare(self):
        if not getattr(self, '_prepared', False):
            self.selector = self.selector or Selector()
            self.fields = self.selector.fields
            # TODO: Different PKs? What about auto-fields?
            if self.is_insert:
                self.fields.add('id')
                # TODO: This could come back to bite me, stomping on
                # the filter like this.
                self.filter = Filter({'id': Placeholder()})
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
        field = self.model_class.Meta.fields[field_name]
        other_model = field.other
        sub_query = Query(
            other_model,
            selector=selector,
            parent=self
        ).prepare()
        self.next_id = sub_query.next_id
        return sub_query

    def update_model(self, result):
        result = result[0]
        if result:
            # TODO: Should recurse for each lookup.
            for name, value in result.items():
                setattr(self.model, name, value)
