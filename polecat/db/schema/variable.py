__all__ = ('SessionVariable',)


class SessionVariable:
    def __init__(self, name, type=None):
        self.name = name
        self.type = type

    def __eq__(self, other):
        return other and self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)
