class Selection:
    def __init__(self, *fields, **lookups):
        self.fields = fields
        self.lookups = lookups

    def __repr__(self):
        return f'<Selector fields="{self.fields}" lookups="{self.lookups}">'

    def __iter__(self):
        for field_name in self.fields:
            yield field_name
        for field_name in self.lookups.keys():
            yield field_name

    def has_lookups(self):
        return bool(self.lookups)

    def all_fields(self):
        return self.fields + tuple(self.lookups.keys())
