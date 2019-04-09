__all__ = ('session',)


class SessionKeyError(KeyError):
    pass


class SessionPlaceholder:
    def __init__(self, session, key):
        self.sesesion = session
        self.key = key

    def evaluate(self):
        return self.session.evaluate(self.key)


class Session:
    def __init__(self):
        self.items = {}

    def __getitem__(self, key):
        return SessionPlaceholder(self, key)

    def evaluate(self, key):
        try:
            return self.items[key]
        except KeyError:
            raise SessionKeyError(f'session does not contain key: {key}')


session = Session()
