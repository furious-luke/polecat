class Entity:
    def __eq__(self, other):
        return not self.has_changed(other)
