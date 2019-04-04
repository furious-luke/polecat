from stdb.core.engine import default_engine as engine

from .coerce import coerce
from .query import Query


class BulkCreate(Query):
    def __init__(self, version, endpoint, data, ignore_duplicates=False):
        super().__init__(version, endpoint)
        self.data = data
        self.ignore_duplicates = ignore_duplicates

    def execute(self):
        sql = self.get_main_sql(self.data)
        ids = engine.execute(sql, len(self.data))
        ids = [x['id'] for x in ids]
        sql = self.get_m2m_sql(self.data, ids)
        engine.execute(sql)
        return ids

    def get_main_sql(self, data):
        assert isinstance(data, list)
        table = self.endpoint['table']
        fields = self.endpoint['fields']

        # Build the set of all field names used across all items to add.
        field_names = set()
        for single_data in data:
            for fn in single_data:
                if fn == 'id':
                    continue
                if fn not in fields:
                    raise ValueError(f'invalid field name: {fn}')
                fld = fields[fn]
                if fld.get('related', False) and 'm2m_table' in fld:
                    continue
                field_names.add(fn)

        # Construct the SQL.
        sql = f'INSERT INTO "{table}" (id'
        for fn in field_names:
            col = fields[fn]['column']
            sql += f',{col}'
        sql += f') VALUES '
        for ii, single_data in enumerate(data):
            if ii != 0:
                sql += ','
            id = single_data.get('id', 'DEFAULT')
            sql += f'({id}'
            for fn in field_names:
                fld = fields[fn]
                if fld.get('related', False):
                    if 'm2m_table' in fld:
                        continue
                if fn in single_data:
                    val = coerce(fld['field']['type'], single_data[fn])
                    val = engine.quote_literal(val)
                else:
                    val = 'DEFAULT'
                sql += f',{val}'
            sql += ')'

        # Ignore duplicates if requested.
        if self.ignore_duplicates:
            sql += ' ON CONFLICT DO NOTHING'

        # Return the IDs.
        sql += ' RETURNING id;'

        return sql

    def get_m2m_sql(self, data, ids):
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
        for single_data, id in zip(data, ids):
            for fn, m2m_table in m2ms:
                val = single_data.get(fn, None)
                if not val:
                    continue
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
