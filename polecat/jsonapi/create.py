from stdb.core.engine import default_engine as engine
from stdb.exceptions import StdbError
from stdb.utils import make_handle, strip_default

from .detail import Detail
from .query import Query


class Create(Query):
    valid_keys = set(['id', 'type', 'attributes', 'relationships'])
    relationship_types = set(['foreignkey', 'manytomany'])

    def __init__(self, version, endpoint, data=None, **kwargs):
        super().__init__(version, endpoint, **kwargs)
        self.data = data
        self._m2ms = []
        self._values = []
        self._replace_m2ms = False
        self._files = []
        self._update = False

    def execute(self):
        sql = self.get_sql()
        if not sql:
            return []
        sql = sql % tuple([
            engine.quote_literal(v)
            for v in self.get_args()
        ])

        try:
            r = engine.execute(sql, 1)
        except engine.plpy.spiexceptions.ForeignKeyViolation:
            raise StdbError('foreign key violation')

        # If any of our fields were files, run an action to confirm
        # each of them has a value in tmpfiles.
        if self._files:
            self.check_files(self._files)

        qry = Detail(self.version, self.endpoint, id=r[0]['id'])
        for r in qry.iter_rows():
            return r[1]

        # Arriving here means we have permission to create but not to
        # get details. Return emptyness.
        return {}

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
        # TODO: Maybe optimise this lookup?
        table = self.endpoint['table']
        field_names, values = self.get_fields_values()
        if not field_names or not values:
            sql = f'INSERT INTO {table} (id) VALUES(DEFAULT) RETURNING id'
        else:
            f_str = ', '.join(field_names)
            v_str = ', '.join(['%s' for _ in values])
            sql = f'INSERT INTO {table} ({f_str}) VALUES({v_str}) RETURNING id'
        return sql

    def get_m2m_sql(self):
        sql = []
        for field_name, m2m_table, values in self._m2ms:
            if self._replace_m2ms:
                sql.append(f'DELETE FROM {m2m_table} USING inserted WHERE lid = inserted.id')
            if values:
                self._values.extend(values)
                v_str = ','.join(f'((SELECT id FROM inserted), %s)' for v in values)
                sql.append(f'INSERT INTO {m2m_table} (lid, rid) VALUES {v_str}')
        return sql

    def get_fields_values(self):
        field_names, values = [], []

        # Extract root-level data.
        try:
            root = self.data['data']
        except (TypeError, KeyError):
            raise StdbError('missing data')

        # Check for an ID first. This is okay as we want to be able
        # to support importing data that comes with IDs. However, we
        # need to ignore it if it's a UUID (TODO: add a link to the
        # relevant section of the JSON-API docs).
        if 'id' in root:
            try:
                v = int(root['id'])
                field_names.append('id')
                values.append(v)
            except ValueError:
                pass

        for key, data in root.items():
            if key == 'attributes':

                for name, value in data.items():

                    # Check for a known field.
                    try:
                        fld = self.endpoint['fields'][name]
                    except KeyError:
                        raise StdbError(f'unknown attribute: {name}')

                    # Must be an attribute.
                    if fld['field']['type'] in self.relationship_types:
                        raise StdbError(f'field is not an attribute: {name}')

                    # If the field is a file, add a post action to confirm the
                    # file exists in our temporary files cache.
                    if fld['field']['type'] == 'file':
                        self._files.append((name, value))

                    values.append(value)
                    field_names.append(fld['column'])

            elif key == 'relationships':

                for name, value in data.items():

                    # Check for a known field.
                    try:
                        fld = self.endpoint['fields'][name]
                    except KeyError:
                        raise StdbError(f'unknown relationship: {name}')

                    # Not allowed to set reverse fields here.
                    if fld['field']['type'] == 'reverse':
                        raise StdbError(f'cannot set reverse relationship: {name}')

                    if fld['field']['type'] == 'manytomany':

                        # Must have the endpoint other set.
                        # TODO: Fix duplicate below.
                        if not fld['other']:
                            raise StdbError('no value for "other" on endpoint')

                        self._m2ms.append((
                            name,
                            fld['m2m_table'],
                            self.parse_manytomany_value(fld, name, value)
                        ))
                    elif fld['field']['type'] == 'foreignkey':

                        # Must have the endpoint other set.
                        if not fld['other']:
                            raise StdbError('no value for "other" on endpoint')

                        values.append(self.parse_foreignkey_value(fld, name, value))
                        field_names.append(fld['column'])
                    else:
                        raise StdbError(f'field is not a relationship: {name}')

            elif key not in self.valid_keys:
                raise StdbError(f'unknown data key: {key}')

        self._values = values
        return field_names, values

    def get_args(self):
        return self._values

    def parse_foreignkey_value(self, field, name, value):
        try:
            v = value['data']
        except (TypeError, KeyError):
            raise StdbError((
                'invalid foreign-key value for "{}": missing "data"'
            ).format(
                name
            ))
        if v is None:
            return None
        try:
            type = make_handle(v['type'])
        except (TypeError, KeyError):
            raise StdbError((
                'invalid foreign-key value for "{}": missing "type"'
            ).format(
                name
            ))
        if type != field['other']:
            raise StdbError((
                'invalid foreign-key value for "{}": should be type "{}"'
            ).format(
                name, strip_default(field['other'])
            ))
        try:
            v = v['id']
        except (TypeError, KeyError):
            raise StdbError((
                'invalid foreign-key value for "{}": missing "id"'
            ).format(
                name
            ))
        return v

    def parse_manytomany_value(self, field, name, value):
        try:
            value = value['data']
        except (TypeError, KeyError):
            raise StdbError((
                'invalid many-to-many value for "{}": missing "data"'
            ).format(
                name
            ))
        if not isinstance(value, list):
            raise StdbError((
                'invalid many-to-many value for "{}": data must be a list'
            ).format(
                name
            ))
        vals = []
        for v in value:
            try:
                type = make_handle(v['type'])
            except (TypeError, KeyError):
                raise StdbError((
                    'invalid many-to-many value for "{}": missing "type"'
                ).format(
                    name
                ))
            if type != field['other']:
                raise StdbError((
                    'invalid many-to-many value for "{}": should be type "{}"'
                ).format(
                    name, strip_default(field['other'])
                ))
            try:
                v = v['id']
            except (TypeError, KeyError):
                raise StdbError((
                    'invalid many-to-many value for "{}": missing "id"'
                ).format(
                    name
                ))
            vals.append(v)
        return vals

    def check_files(self, files):
        """ Confirm each entry in files exists in the "tmpfiles" table.

        Also deletes those entries from the table.
        """
        if self._update:
            raise StdbError('updating files not implemented yet')
        dp_id = self.endpoint['datapoint_id']
        where = ' OR '.join([
            '(field = {} AND path = {})'.format(
                engine.quote_literal(f),
                engine.quote_literal(p)
            )
            for f, p in files
        ])
        sql = (
            'DELETE FROM file.tmpfiles'
            ' WHERE datapoint = {}'
            ' AND ({})'
            ' RETURNING field'
        ).format(
            engine.quote_literal(dp_id),
            where,
            engine.quote_literal([f[1] for f in files])
        )
        rslts = engine.execute(sql, len(files))
        missing = set([f[0] for f in files]) - set([r['field'] for r in rslts])
        if len(missing):
            raise StdbError('invalid files given for: {}'.format(', '.join(missing)))
