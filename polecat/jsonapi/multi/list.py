from urllib.parse import parse_qs, urlencode, urlsplit

import ujson

from ..list import List as ListBase

# from stdb.core.engine import default_engine as engine
# from stdb.core.file import make_field_path, presign_get



class List(ListBase):
    """ Use multi-staged queries.

    SELECT
     id,
     name,
     array_to_jsonb(array_agg(actors.right_id))
    FROM movies
    LEFT JOIN LATERAL (
     SELECT
      right_id
     FROM m2m_table_actors
     WHERE
      left_id = movies.id
     LIMIT 20
    ) AS actors ON true
    LIMIT 20;

    SELECT
     id,
     name,
     array_to_jsonb(array_agg(rented.right_id))
    FROM people
    ...
    WHERE
     people.id IN VALUES(...)
    LIMIT 20
    """

    def iter_main_rows(self):
        sql = self.get_main_sql(self.endpoint)
        self._unique = {}
        m2ms = self.get_m2m_indices(self.endpoint)
        self._ids = dict([(n, set()) for n, m, t in m2ms])
        sql = sql % tuple([
            engine.quote_literal(v)
            for v in self.values
        ])
        for row in engine.cursor(sql):
            self.parse_row(row, self.endpoint)
            self._unique[self.endpoint['type']].add(row['id'])
            self._add_m2m_ids(m2ms, row)
            yield (self.endpoint['type'], row)

    def iter_included_rows(self):
        for field_name, path, endpoint in self.iter_paths():
            self._unique.setdefault(endpoint['type'], set())
            m2ms = self.get_m2m_indices(endpoint)
            full_path = f'{path}{field_name}'
            self._ids.update(dict([(f'{full_path}.{n}', set()) for n, m, t in m2ms]))
            if self._ids[full_path]:
                sql = self.get_include_sql(endpoint, self._ids[full_path])
                for row in engine.cursor(sql):
                    self.parse_row(row, endpoint)
                    self._add_m2m_ids(m2ms, row, f'{full_path}.')
                    if row['id'] not in self._unique[endpoint['type']]:
                        self._unique[endpoint['type']].add(row['id'])
                        yield (endpoint['type'], row)

    def parse_row(self, row, endpoint):
        for n in endpoint['fields']:
            field = endpoint['fields'][n]
            other = field.get('other', None)
            if other:
                # TODO: Use "many" to indicate reverse or m2m
                many = 'm2m_table' in field or field['field']['type'] == 'reverse'
                if many:
                    if row[n]:
                        row[n] = ujson.loads(row[n])
            elif field.get('field', {}).get('type', None) == 'json':
                if row[n]:
                    row[n] = ujson.loads(row[n])
            elif field.get('field', {}).get('type', None) == 'file':
                fld_key = endpoint['fields'][n]['fieldkey']
                path = make_field_path(row[n], fld_key)
                row[n] = presign_get(path)

    def get_main_sql(self, endpoint):
        self.values = []
        sql = (
            'SELECT {fields_sql}'
            ' FROM {db_table}'
            ' {m2m_joins}'
            ' {where_sql}'
            ' {order_sql}'
            '{offset_sql}'
            '{limit_sql}'
        ).format(
            fields_sql=self.get_select_fields(endpoint),
            db_table=endpoint['table'],
            m2m_joins=self.get_m2m_joins(endpoint),
            where_sql=self.get_where_sql(endpoint),
            order_sql=self.get_main_order_sql(),
            offset_sql=self.get_main_offset_sql(),
            limit_sql=self.get_main_limit_sql()
        )
        return sql

    def get_include_sql(self, endpoint, parent_ids):
        sql = (
            'SELECT {fields_sql}'
            ' FROM {db_table}'
            ' {m2m_joins}'
            ' WHERE {db_table}.id = ANY(ARRAY[{ids}])'
            ' {order_sql}'
            ' {limit_sql};'
        ).format(
            fields_sql=self.get_select_fields(endpoint),
            db_table=endpoint['table'],
            m2m_joins=self.get_m2m_joins(endpoint),
            ids=', '.join(f'{id}' for id in parent_ids),
            order_sql=self.get_include_order_sql(),
            limit_sql=self.get_include_limit_sql()
        )
        return sql

    def get_main_order_sql(self):
        sql = []
        for o in self.order:
            mod = ''
            if o[0] == '-':
                mod = ' DESC'
                o = o[1:]
            else:
                mod = ' ASC'
            sql.append(f'{o}{mod}')
        if sql:
            return 'ORDER BY ' + ', '.join(sql)
        else:
            return ''

    def get_include_order_sql(self):
        # TODO: Make more general
        if len(self.order) and self.order[0] == 'id':
            return 'ORDER BY id'
        else:
            return ''

    def get_m2m_order_sql(self, other_table):
        # TODO: Make more general
        if len(self.order) and self.order[0] == 'id':
            return f'ORDER BY {other_table}.id'
        else:
            return ''

    def get_select_fields(self, endpoint):
        """ Product the SQL needed to extract all fields from an endpoint.
        """
        table = endpoint['table']
        fields = [f'{table}.id']
        fields.extend(
            self.get_select_field(endpoint, endpoint['fields'][n], n)
            for n in endpoint['fields']
        )
        sql = ', '.join(fields)
        return sql

    def get_select_field(self, model, field, field_name):
        """ Produce the SQL needed to extract a field from an endpoint.
        """

        # Get the SQL for either an attribute (or FK) or an M2M.
        if 'column' in field:
            tbl = model.Meta.table
            col = field['column']
            sql = f'{tbl}.{col}'
        else:
            sql = f'"{field_name}".id'

        # Check for a transformation.
        xform = field.get('transform')
        if xform:
            sql = f'{xform}({sql})'

        # Always force the field name.
        sql = f'{sql} AS "{field_name}"'

        return sql

    def get_m2m_joins(self, endpoint):
        sql = ' '.join(
            self.get_m2m_join(endpoint, endpoint['fields'][n], n)
            for n in endpoint['fields']
            if 'm2m_table' in endpoint['fields'][n] or endpoint['fields'][n]['field']['type'] == 'reverse'
        )
        return sql

    def get_m2m_join(self, endpoint, field, field_name):
        if 'm2m_table' in field:
            sql = (
                'LEFT JOIN LATERAL ('
                ' SELECT array_to_json(array_agg(rid)) AS id'
                ' FROM {m2m_table}'
                ' WHERE lid = {db_table}.id'
                ' {order_sql}'
                ' {limit_sql}'
                ') AS "{field_name}" ON true'
            ).format(
                m2m_table=field['m2m_table'],
                db_table=endpoint['table'],
                order_sql=self.get_m2m_order_sql(endpoint['table']),
                limit_sql=self.get_include_limit_sql(),
                field_name=field_name
            )
        else:
            sql = (
                'LEFT JOIN LATERAL ('
                ' SELECT array_to_json(array_agg({other_table}.id)) AS id'
                ' FROM {other_table}'
                ' WHERE {other_table}.{other_column} = {db_table}.id'
                ' {order_sql}'
                ' {limit_sql}'
                ') AS "{field_name}" ON true'
            ).format(
                other_table=field['other_table'],
                other_column=field['other_column'],
                db_table=endpoint['table'],
                order_sql=self.get_m2m_order_sql(endpoint['table']),
                limit_sql=self.get_include_limit_sql(),
                field_name=field_name
            )
        return sql

    def get_main_offset_sql(self):
        if self.offset:
            return f' OFFSET {self.offset}'
        else:
            return ''

    def get_main_limit_sql(self):
        if self.limit:
            return f' LIMIT {self.limit}'
        else:
            return ''

    def get_include_limit_sql(self):
        if self.include_limit:
            return f' LIMIT {self.include_limit}'
        else:
            return ''

    def get_m2m_indices(self, endpoint):
        m2ms = []
        self._unique.setdefault(endpoint['type'], set())
        for n in endpoint['fields']:
            field = endpoint['fields'][n]
            other = field.get('other', None)
            if not other:
                continue
            # TODO: Use "many" to indicate reverse or m2m
            many = 'm2m_table' in field or field['field']['type'] == 'reverse'
            m2ms.append((n, many, other))
            self._unique.setdefault(other, set())
        return m2ms

    def _add_m2m_ids(self, m2ms, row, prefix=''):
        for n, many, type in m2ms:
            path = f'{prefix}{n}'
            val = row[n]
            if val is not None:
                if many:
                    for id in val:
                        self._ids[path].add(id)
                else:
                    self._ids[path].add(val)

    def get_links_row(self):
        """ Determine our next and prev links.
        """
        url_data = urlsplit(self.url)
        qs_data = parse_qs(url_data.query)

        if not self.limit:
            return None

        next_offs = (self.offset or 0) + self.limit
        prev_offs = (self.offset or 0) - self.limit

        # TODO: Check against max?
        qs_data['page[offset]'] = next_offs
        next = url_data._replace(query=urlencode(qs_data, True)).geturl()

        if prev_offs >= 0:
            qs_data['page[offset]'] = prev_offs
            prev = url_data._replace(query=urlencode(qs_data, True)).geturl()
        else:
            prev = 'null'

        return {
            'next': next,
            'prev': prev
        }
