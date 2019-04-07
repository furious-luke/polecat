class Selector:
    def __init__(self, *fields, **lookups):
        self.fields = set(fields)
        self.lookups = lookups

    def __repr__(self):
        return f'<Selector fields="{self.fields}" lookups="{self.lookups}">'

    def all_fields(self):
        return self.fields.union(set(self.lookups.keys()))
