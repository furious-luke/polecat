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

    def copy(self):
        return Selection(*self.fields, **self.lookups)

    def get(self, name, force=False):
        return self.lookups.get(name) or (Selection() if force else None)

    def merge(self, other):
        if other is not None:
            self.fields = list(set(self.fields) | set(other.fields))
            self.lookups = {**self.lookups}
            for name, sub in other.lookups.items():
                self.lookups[name] = self.lookups.get(name, Selection()).merge(sub)
        return self

    def has_lookups(self):
        return bool(self.lookups)

    def all_fields(self):
        return self.fields + tuple(self.lookups.keys())
