from stdb.core.engine import default_engine as engine

from .query import Query
from .coerce import coerce


class BulkUpdate(Query):
    def __init__(self, version, endpoint, data):
        super().__init__(version, endpoint)
        self.data = data

    def execute(self):
        sql = self.get_main_sql(self.data)
        if sql:
            engine.execute(sql, len(self.data))
        sql = self.get_m2m_sql(self.data)
        if sql:
            engine.execute(sql)

    def get_main_sql(self, data):
        assert isinstance(data, list)
        table = self.endpoint['table']
        fields = self.endpoint['fields']

        # Construct the SQL.
        sql = ''
        for single_data in data:
            id = single_data['id']
            ii = 0
            sub_sql = ''
            for fn in single_data:
                if fn == 'id':
                    continue
                try:
                    fld = fields[fn]
                except KeyError:
                    raise ValueError(f'invalid field name: {fn}')
                if fld.get('related', False):
                    if 'm2m_table' in fld:
                        continue
                val = coerce(fld['field']['type'], single_data[fn])
                val = engine.quote_literal(val)
                col = fields[fn]['column']
                if ii > 0:
                    sub_sql += ','
                sub_sql += '{}={}'.format(col, val)
                ii += 1
            if sub_sql:
                sql += f'UPDATE "{table}" SET '
                sql += sub_sql
                sql += f' WHERE id={id};'

        return sql

    def get_m2m_sql(self, data):
        assert isinstance(data, list)
        fields = self.endpoint['fields']

        # Collect the set of m2m fields and the m2m table it goes with.
        m2ms = []
        for fn, fld in fields.items():
            fld = fields[fn]
            if fld.get('related', False) and 'm2m_table' in fld:
                m2ms.append((fn, fld['m2m_table']))

        # Contruct the sequence of inserts required to populate M2M
        # values.
        sql = ''
        for single_data in data:
            for fn, m2m_table in m2ms:
                val = single_data.get(fn, None)
                if not val:
                    continue
                id = single_data['id']
                if not isinstance(val, list):
                    raise ValueError('invalid many-to-many value, should be a list')
                sql += f'INSERT INTO "{m2m_table}" (lid, rid) VALUES '
                for ii, v in enumerate(val):
                    if not isinstance(v, int):
                        raise ValueError('invalid related ID, should be an integer')
                    if ii > 0:
                        sql += ','
                    sql += f'({id},{v})'
                sql += ';'

        return sql
