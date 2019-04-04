from .query import Query
from .utils import strip_default


class List(Query):
    def __init__(self, model,
                 include=None, filter=None, order=None,
                 limit=None, include_limit=None,
                 offset=None, offset_reverse=False,
                 url=None,
                 **kwargs):
        super().__init__(model, **kwargs)
        self.include = include or []
        self.filter = filter
        self.order = order or ['id']  # default ordering for pagination
        self.limit = limit
        self.include_limit = include_limit
        self.offset = offset
        self.offset_reverse = offset_reverse
        self.url = url

    def iter_rows(self):
        for r in self.iter_main_rows():
            yield (
                'm',
                self._row_to_object(r)
            )
        for r in self.iter_included_rows():
            yield (
                'i',
                self._row_to_object(r)
            )
        if self.url:
            r = self.get_links_row()
            if r is not None:
                yield ('l', r)

    def iter_main_rows(self):
        raise NotImplementedError

    def iter_included_rows(self):
        raise NotImplementedError

    def iter_paths(self):
        if not hasattr(self, '_include_tree'):
            self._include_tree = self._make_include_tree()
        def _recurse(node, model, path=''):
            for k, v in node.items():
                try:
                    next_field = model.Meta.fields[k]
                except KeyError:
                    raise ValueError(
                        f'invalid include: {model} has no field {k}'
                    )
                try:
                    next_model = next_field.other
                except AttributeError:
                    raise ValueError(f'invalid include: included field is not a relationship')
                yield (k, path, next_model)
                for r in _recurse(v, next_model, f'{path}{k}.'):
                    yield r
        for r in _recurse(self._include_tree, self.model):
            yield r

    def _make_include_tree(self):
        tree = {}
        def _recurse(node, path, ii=0):
            p = path[ii]
            next = node.setdefault(p, {})
            if ii + 1 < len(path):
                _recurse(next, path, ii + 1)
        for i in self.include:
            path = i.split('.')
            _recurse(tree, path)
        return tree

    # async def respond(self, cursor):
    #     data = {'data': [], 'included': []}
    #     async for row in self.iter_main_rows(cursor):
    #         r = self._row_to_object(row)
    #         data['data'].append(r)
    #     unique = set()
    #     async for row in self.iter_included_rows(cursor):
    #         r = self._row_to_object(row, unique)
    #         if r:
    #             data['included'].append(r)
    #     if self.single:
    #         if len(data['data']):
    #             data['data'] = data['data'][0]
    #         else:
    #             data['data'] = None
    #     if not len(data['included']):
    #         del data['included']
    #     return data

    def _row_to_object(self, row, unique=None):
        id = row[1]['id']
        ident = (row[0], id)
        if unique:
            if ident in unique:
                return None
            unique.add(ident)
        ep = self.version[row[0]]
        attrs, rels = self._make_row_values(ep, row[1])
        # TODO: Need to decide on using system prefixed endpoints
        # or a flat namespace.
        obj = {
            'type': strip_default(row[0]),
            'id': id,
            'attributes': attrs,
            'relationships': rels
        }
        return obj

    def _make_row_values(self, model, row):
        attrs = {}
        rels = {}
        for field_name in model.Meta.fields.keys():
            value = row[field_name]
            field = model.Meta.fields[field_name]

            # The other type name should be that of the included endpoint.
            # However, there may not be an included endpoint, so what then?
            # Am currently setting to the value of the datapoint type, which
            # may be okay but seems suspect.
            # TODO: find alternative?
            other = getattr(field, 'other', None)

            if other:
                # TODO
                many = 'm2m_table' in field or field['field']['type'] == 'reverse'
                if many:
                    if value is None or value[0] is None:
                        rels[field_name] = {'data': []}
                    else:
                        rels[field_name] = {
                            'data': [
                                {'type': strip_default(other), 'id': v}
                                for v in value
                            ]
                        }
                else:
                    if value is None:
                        rels[field_name] = {'data': None}
                    else:
                        rels[field_name] = {
                            'data': {
                                'type': strip_default(other),
                                'id': value
                            }
                        }
            else:
                attrs[field_name] = value
        return attrs, rels
