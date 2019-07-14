from polecat.db.schema.variable import SessionVariable

__all__ = ('session',)


class Session:
    def __getitem__(self, key):
        return SessionVariable(key)

    def __call__(self, key, type):
        return SessionVariable(key, type)


session = Session()
