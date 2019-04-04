class Selector:
    def __init__(self, *fields, **lookups):
        self.fields = fields
        self.lookups = lookups

    def __repr__(self):
        return f'<Selector fields="{self.fields}" lookups="{self.lookups}">'
