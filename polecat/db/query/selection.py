class Selection:
    def __init__(self, *fields, **lookups):
        self.fields = set(fields)
        self.lookups = lookups

    def __repr__(self):
        return f'<Selector fields="{self.fields}" lookups="{self.lookups}">'

    def __iter__(self):
        # TODO: Could be more efficient.
        return iter(self.all_fields())

    def all_fields(self):
        return self.fields.union(set(self.lookups.keys()))
