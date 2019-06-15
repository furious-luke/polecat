from ...utils.repr import to_repr
from .entity import Entity


class Role(Entity):
    def __init__(self, name, parents=None, options=None, app=None):
        self.app = app
        self.name = name
        self.parents = parents or ()
        self.options = options or {}

    def __repr__(self):
        return to_repr(
            self,
            name=self.name
        )

    @property
    def signature(self):
        return (Role, self.name)

    def has_changed(self, other):
        return (
            self.name != other.name or
            self.has_changed_parents(other)
        )

    def has_changed_parents(self, other):
        # TODO: I don't like this much.
        return (
            sorted(p.name for p in self.parents) !=
            sorted(p.name for p in other.parents)
        )


class Access(Entity):
    def __init__(self, entity, all=None, select=None, insert=None, update=None,
                 delete=None, app=None):
        self.entity = entity
        self.all = all or ()
        self.select = select or ()
        self.insert = insert or ()
        self.update = update or ()
        self.delete = delete or ()
        self.app = app

    def __repr__(self):
        return to_repr(
            self,
            name=self.entity if isinstance(self.entity, str) else self.entity.name  # TODO: Need an interface.
        )

    @property
    def signature(self):
        return (Access, self.entity.signature)

    def has_changed(self, other):
        return (
            self.entity != other.entity or
            self.all != other.all or
            self.select != other.select or
            self.insert != other.insert or
            self.update != other.update or
            self.delete != other.delete
        )
