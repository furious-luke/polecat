# from .filter import Filter


class Query:
    def __init__(self, model):
        self.model = model
        self.page_size = 20

    def iter_rows(self):
        raise NotImplementedError

    def get_where_sql(self, model):
        flt = getattr(self, 'filter', None)
        # if 'default_filter' in endpoint:
        #     def_flt = Filter(endpoint['default_filter'])
        #     if flt:
        #         flt.merge(def_flt)
        #     else:
        #         flt = def_flt
        if flt:
            flt = self.filter.get_sql(self.version, self.endpoint)
            if flt:
                return f'WHERE {flt}'
        return ''
