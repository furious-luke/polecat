from sanic.response import json_dumps

from .utils import ApiError


class JsonApiError(ApiError):
    pass


def validate(data, update=False):
    try:
        dat = data['data']
    except:
        raise JsonApiError(400, 'missing root data')
    try:
        type = dat['type']
    except:
        raise JsonApiError(400, 'root data is missing type')
    if update:
        try:
            type = dat['id']
        except:
            raise JsonApiError(400, 'root data is missing id')
    rels = dat.get('relationships', None)
    if rels is not None:
        if not isinstance(rels, dict):
            raise JsonApiError(400, 'invalid relationship data')
        for fn, values in rels.items():
            if not isinstance(values, list):
                values = [values]
            for val in values:
                if not isinstance(val, dict):
                    raise JsonApiError(400, f'invalid related data for {fn}')
                if 'data' not in val:
                    raise JsonApiError(400, f'invalid related data for {fn}')
                valdat = val['data']
                if isinstance(valdat, dict) and 'id' not in valdat:
                    raise JsonApiError(400, f'no id specified for {fn}')
    # try:
    #     attrs = dat['attributes']
    # except:
    #     raise JsonApiError(400, 'root data is missing attributes')
    # try:
    #     rels = dat['relationships']
    # except:
    #     raise JsonApiError(400, 'root data is missing relationships')


class Query:
    def __init__(self, revision, endpoint):
        self.revision = revision
        self.endpoint = endpoint

    async def execute(self, cursor, response=None):
        await cursor.execute(self.get_sql(), self.get_args())
        if response:
            await self.respond(response, cursor)
        else:
            return await self.respond_data(cursor)

    def get_sql(self):
        raise NotImplemented

    def get_args(self):
        return ()

    async def respond_data(self, cursor):
        pass


class List(Query):
    def __init__(self, revision, endpoint, include=[], single=False):
        self.revision = revision
        self.endpoint = endpoint
        self.include = include
        self.single = single

    def get_sql(self):
        sql = getattr(self, '_sql', None)
        if not sql:
            self._aliases, self._subselects = self.get_components()
            cte = self.get_cte(self._subselects)
            main = self.get_main_select(self._aliases)
            sql = f'{cte} {main}'
            self._sql = sql
        return sql

    async def respond(self, response, cursor):
        primary = []
        included = []
        if self.single:
            response.write('{"data":')
        else:
            response.write('{"data":[')
        prev_included = False
        join = False
        unique = set()
        async for row in cursor:
            ident = (row[1], row[2])
            if ident in unique:
                continue
            unique.add(ident)
            attrs, rels = self.match_row_values(row[1], row[3])
            obj = {
                'type': row[1],
                'id': row[2],
                'attributes': attrs,
                'relationships': rels
            }
            if row[0] == 'f':
                if join:
                    response.write(',' + json_dumps(obj))
                else:
                    response.write(json_dumps(obj))
                    join = True
            else:
                if not prev_included:
                    if self.single:
                        response.write(',"included":[')
                    else:
                        response.write('],"included":[')
                    prev_included = True
                    join = False
                if join:
                    response.write(',' + json_dumps(obj))
                else:
                    response.write(json_dumps(obj))
                    join = True
        if self.single and not self.include:
            response.write('}')
        else:
            response.write(']}')

    async def respond_data(self, cursor):
        data = {'data': [], 'included': []}
        unique = set()
        async for row in cursor:
            ident = (row[1], row[2])
            if ident in unique:
                continue
            unique.add(ident)
            attrs, rels = self.match_row_values(row[1], row[3])
            obj = {
                'type': row[1],
                'id': row[2],
                'attributes': attrs,
                'relationships': rels
            }
            if row[0] == 'f':
                data['data'].append(obj)
            else:
                data['included'].append(obj)
        if self.single:
            if len(data['data']):
                data['data'] = data['data'][0]
            else:
                data['data'] = None
        if not len(data['included']):
            del data['included']
        return data

    def get_components(self, where=''):
        aliases = []
        subselects = []
        name_index = 0

        def get_alias():
            nonlocal name_index
            alias = f'ep{name_index}'
            name_index += 1
            return alias

        def recurse(endpoint, alias, path, path_index=0):
            nonlocal aliases, subselects
            field_name = path[path_index]
            try:
                field = endpoint.fields[field_name]
                incl = endpoint.include[field_name]
                other = self.revision.endpoints[incl]
            except KeyError:
                raise ApiError(400, 'invalid include', field_name)
            other_alias = get_alias()
            aliases.append(other_alias)
            subselects.append(
                self.get_subselect(
                    other_alias,
                    other,
                    alias,
                    endpoint.field_indices[field_name],
                    included=True,
                    prev_is_many=field.get('many', False)
                )
            )
            path_index += 1
            if path_index < len(path):
                recurse(other, other_alias, path, path_index)

        alias = get_alias()
        aliases.append(alias)
        subselects.append(
            self.get_subselect(
                alias,
                self.endpoint,
                where=where
            )
        )

        for incl in self.include:
            path = incl.split('.')
            recurse(self.endpoint, alias, path)

        return aliases, subselects

    def get_subselect(self, alias, endpoint,
                      prev_alias=None, prev_field_index=None, included=False,
                      where='', prev_is_many=False):
        type_name = endpoint.type_name
        table_name = endpoint.table_name
        page_size = endpoint.default_page_size

        ids_str = self.get_subselect_ids(alias, table_name, page_size, prev_alias, prev_field_index, where=where, prev_is_many=prev_is_many)

        field_selects = [
            self.get_subselect_field(alias, endpoint, fn)
            for fn in endpoint.field_names
        ]
        fields_str = ', '.join(field_selects)

        included = 't' if included else 'f'
        select_str = (
            'SELECT'
            '  cast(\'{included}\' AS text),'
            '  cast(\'{type_name}\' AS text),'
            '  {table_name}.id,'
            '  json_build_array({fields_str})'
        ).format(
            included=included,
            type_name=type_name,
            table_name=table_name,
            fields_str=fields_str
        )

        where_str = (
            ' INNER JOIN'
            '  {alias}_ids ON {table_name}.id = {alias}_ids.id'
        ).format(
            alias=alias,
            table_name=table_name
        )
        for fn in endpoint.field_names:
            field = endpoint.fields[fn]
            if field.get('many', False):
                where_str += ' ' + self.get_subselect_where(alias, fn, endpoint)

        return f'{alias}_ids(id) AS ({ids_str}), {alias}(incl, type, id, fields) AS ({select_str} FROM {table_name}{where_str})'

    def get_subselect_ids(self, alias, table_name, page_size, prev_alias=None, prev_field_index=None, where='', prev_is_many=False):

        if prev_alias and prev_field_index is not None:
            if prev_is_many:
                where_str = (
                    ' INNER JOIN'
                    '  {prev_alias} ON {table_name}.id IN (SELECT value::text::int FROM json_array_elements({prev_alias}.fields->{prev_field_index}))'
                ).format(
                    prev_alias=prev_alias,
                    prev_field_index=prev_field_index,
                    table_name=table_name
                )
            else:
                where_str = (
                    ' INNER JOIN'
                    '  {prev_alias} ON {table_name}.id = cast({prev_alias}.fields->>{prev_field_index} AS int)'
                ).format(
                    prev_alias=prev_alias,
                    prev_field_index=prev_field_index,
                    table_name=table_name
                )
            if where:
                where_str += f' AND {where}'
            distinct = ' DISTINCT'
        else:
            where_str = where
            distinct = ''

        sql = (
            'SELECT{distinct}'
            '  {table_name}.id'
            ' FROM'
            '  {table_name}'
            '{where_str}'
            ' LIMIT'
            '  {page_size}'
        ).format(
            distinct=distinct,
            alias=alias,
            table_name=table_name,
            page_size=page_size,
            where_str=where_str
        )
        return sql

    def get_subselect_field(self, alias, endpoint, field_name):
        field = endpoint.fields[field_name]
        if field.get('many', False):
            sql = f'{field_name}.values'
        else:
            sql = field['db_field']
        return sql

    def get_subselect_where(self, alias, field_name, endpoint):
        field = endpoint.fields[field_name]
        m2m_table = field['m2m_db_table']
        sql = (
            'INNER JOIN ('
            ' SELECT'
            '   {alias}_ids.id AS id,'
            '   array_to_json(array_agg(right_id)) AS values'
            '  FROM'
            '   {alias}_ids'
            '  LEFT JOIN'
            '   {m2m_table} ON left_id = {alias}_ids.id'
            '  GROUP BY {alias}_ids.id'
            '  LIMIT {page_size}'
            ') AS {field_name} ON {field_name}.id = {alias}_ids.id'
        ).format(
            m2m_table=m2m_table,
            alias=alias,
            page_size=endpoint.default_page_size,
            field_name=field_name
        )
        return sql

    def get_cte(self, subselects):
        joined = ', '.join(subselects)
        return f'WITH {joined}'

    def get_main_select(self, aliases, where=''):
        unions = ' UNION ALL '.join(
            f'SELECT * FROM {a}'
            for a in aliases
        )
        if not self.include:
            return f'{unions}{where};'
        else:
            return f'SELECT * FROM ({unions}){where} AS tmp;'

    def match_row_values(self, type_name, values):
        ep = self.revision.endpoints[type_name]
        attrs = {}
        rels = {}
        for field_name, value in zip(ep.field_names, values):
            field = ep.fields[field_name]

            # The other type name should be that of the included endpoint.
            # However, there may not be an included endpoint, so what then?
            # Am currently setting to the value of the datapoint type, which
            # may be okay but seems suspect.
            # TODO: find alternative?
            other = ep.include.get(field_name, field.get('other', None))

            if other:
                if field.get('many', False):
                    if value is None or value[0] is None:
                        rels[field_name] = []
                    else:
                        rels[field_name] = {
                            'data': [
                                {'type': other, 'id': v}
                                for v in value
                            ]
                        }
                else:
                    if value is None:
                        rels[field_name] = value
                    else:
                        rels[field_name] = {
                            'data': {
                                'type': other,
                                'id': value
                            }
                        }
            else:
                attrs[field_name] = value
        return attrs, rels


class Detail(List):
    def __init__(self, revision, endpoint, id, include=[]):
        self.id = id
        super().__init__(revision, endpoint, include, single=True)

    def get_sql(self):
        sql = getattr(self, '_sql', None)
        if not sql:
            where = f' WHERE id = {self.id}'
            self._aliases, self._subselects = self.get_components(where=where)
            cte = self.get_cte(self._subselects)
            main = self.get_main_select(self._aliases)
            sql = f'{cte} {main}'
            self._sql = sql
        return sql


class Create:
    def __init__(self, revision, endpoint, data={}):
        self.revision = revision
        self.endpoint = endpoint
        self.data = data
        self._m2ms = []
        self._values = []

    async def execute(self, cursor, response=None):
        sql = self.get_sql()
        if not sql:
            return
        await cursor.execute(sql, self.get_args())
        id = await cursor.fetchone()
        qry = Detail(self.revision, self.endpoint, id=id[0])
        return await qry.execute(cursor, response)

    def get_sql(self):
        sql = self.get_main_sql()
        m2m_sql = self.get_m2m_sql()
        if m2m_sql:
            if sql:
                m2m_parts = ', '.join(f't{i} AS ({m})' for i, m in enumerate(m2m_sql))
                sql = f'WITH inserted AS ({sql}), {m2m_parts} SELECT id FROM inserted;'
            else:
                sql = '; '.join(m2m_sql)
        return sql

    def get_main_sql(self):
        table = self.endpoint.table_name
        field_names, values = self.get_fields_values()
        if not field_names or not values:
            sql = f'INSERT INTO {table}(id) VALUES(DEFAULT) RETURNING id'
        else:
            f_str = ', '.join(field_names)
            v_str = ', '.join(['%s' for _ in values])
            sql = f'INSERT INTO {table}({f_str}) VALUES({v_str}) RETURNING id'
        return sql

    def get_m2m_sql(self):
        sql = []
        for field_name, m2m_table, values in self._m2ms:
            sql.append(f'DELETE FROM {m2m_table} USING inserted WHERE left_id = inserted.id')
            try:
                if values:
                    self._values.extend(v['id'] for v in values)
                    v_str = ','.join(f'((SELECT id FROM inserted), %s)' for v in values)
                    sql.append(f'INSERT INTO {m2m_table}(left_id, right_id) VALUES {v_str}')
            except KeyError:
                raise JsonApiError(400, 'missing id in m2m')
        return sql

    def get_fields_values(self):
        field_names, values = [], []
        try:
            data = self.data['data'] or {}
        except:
            raise JsonApiError(400, 'missing root data')
        attributes = data.get('attributes', {}) or {}
        relationships = data.get('relationships', {}) or {}
        for name, field in self.endpoint.fields.items():
            has_other = 'other' in field
            if has_other and field.get('many', False):
                if name in relationships:
                    self._m2ms.append(
                        (
                            name,
                            field['m2m_db_table'],
                            relationships[name]['data']
                        )
                    )
            else:
                if has_other:
                    if name in relationships:
                        # TODO: check type
                        try:
                            val = self.data['data']['relationships'][name]['data']['id']
                        except:
                            val = None
                        values.append(val)
                        field_names.append(field['db_field'])
                else:
                    if name in attributes:
                        values.append(self.data['data']['attributes'][name])
                        field_names.append(field['db_field'])
        self._values = values
        return field_names, values

    def get_args(self):
        return self._values


class Update(Create):
    def __init__(self, revision, endpoint, id, data={}):
        super().__init__(revision, endpoint, data)
        self._id = id

    def get_main_sql(self):
        table = self.endpoint.table_name
        field_names, values = self.get_fields_values()
        fv_str = ', '.join(f'{f} = %s' for f in field_names)
        if not fv_str:
            return ''
        sql = f'UPDATE {table} SET {fv_str} WHERE id = {self._id} RETURNING id'
        return sql

    def get_m2m_sql(self):
        sql = []
        for field_name, m2m_table, values in self._m2ms:
            sql.append(f'DELETE FROM {m2m_table} WHERE left_id = {self._id}')
            try:
                if values:
                    self._values.extend(v['id'] for v in values)
                    v_str = ','.join(f'({self._id}, %s)' for v in values)
                    sql.append(f'INSERT INTO {m2m_table}(left_id, right_id) VALUES {v_str}')
            except:
                raise JsonApiError(400, 'missing id in m2m')
        sql.append(f'SELECT {self._id}')
        return sql


class Delete(Query):
    def __init__(self, revision, endpoint, id):
        super().__init__(revision, endpoint)
        self.id = id

    def get_sql(self):
        table_name = self.endpoint.table_name
        return f'DELETE FROM {table_name} WHERE id = {self.id};'
