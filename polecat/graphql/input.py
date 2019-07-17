class Input:
    def __init__(self, type=None, input=None):
        if type is not None and input is not None:
            self.translate(type, input)

    def translate(self, type, input):
        self.change = {}
        self.delete = {}
        for cc_name, graphql_field in type.fields.items():
            field = graphql_field._field
            change, delete = field.from_input(input, type)
            if change:
                self.change.update(change)
            if delete:
                self.merge_delete(delete)

    def merge_delete(self, delete, source=None):
        if not source:
            source = self.delete
        for model, ids in delete.items():
            source.setdefault(model, set()).update(ids)


def parse_id(id):
    if id is None:
        return id
    try:
        return int(id)
    except ValueError:
        raise ValueError(f'Cannot parse ID: {id}')
