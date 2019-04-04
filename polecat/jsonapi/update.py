from . import Create


class Update(Create):
    def __init__(self, version, endpoint, id, data={}, replace_m2ms=True, **kwargs):
        super().__init__(version, endpoint, data, **kwargs)
        self._id = id
        self._replace_m2ms = replace_m2ms
        self._update = True

    def get_main_sql(self):
        table = self.endpoint['table']
        field_names, values = self.get_fields_values()
        fv_str = ', '.join(f'{f} = %s' for f in field_names)
        if not fv_str:
            return ''
        sql = f'UPDATE {table} SET {fv_str} WHERE id = {self._id} RETURNING id'
        return sql

    # TODO: Should this just be the create one?
    def get_m2m_sql(self):
        sql = super().get_m2m_sql()
        # for field_name, m2m_table, values in self._m2ms:
        #     if self._replace_m2ms:
        #         sql.append(f'DELETE FROM {m2m_table} WHERE left_id = {self._id}')
        #     if values:
        #         self._values.extend(values)
        #         v_str = ','.join(f'({self._id}, %s)' for v in values)
        #         sql.append(f'INSERT INTO {m2m_table}(left_id, right_id) VALUES {v_str}')
        sql.append(f'SELECT {self._id}')
        return sql
