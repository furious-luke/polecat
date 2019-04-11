from ..utils import to_tuple
from .exceptions import InvalidFieldError
from .registry import (ModelMetaclass, MutationMetaclass, QueryMetaclass,
                       RoleMetaclass, TypeMetaclass)


# TODO: Types and models are soooo similar, perhaps use a better
# architecture than total separation?
class Type(metaclass=TypeMetaclass):
    def __init__(self, **kwargs):
        for field_name, value in kwargs.items():
            setattr(self, field_name, value)

    def __repr__(self):
        return f'<{self.Meta.name}>'


class Model(metaclass=ModelMetaclass):
    def __init__(self, **kwargs):
        for field_name, value in kwargs.items():
            try:
                field = self.Meta.fields[field_name]
            except KeyError:
                raise InvalidFieldError(self.__class__, field_name)
            setattr(self, field_name, field.from_incoming(self, value))

    def __repr__(self):
        return f'<{self.Meta.name}>'


class Role(metaclass=RoleMetaclass):
    pass


class Access:
    def __init__(self, all=None,
                 select=None,
                 insert=None, update=None,
                 delete=None):
        self.all = to_tuple(all)
        self.select = to_tuple(select)
        self.insert = to_tuple(insert)
        self.update = to_tuple(update)
        self.delete = to_tuple(delete)


class Query(metaclass=QueryMetaclass):
    pass


class Mutation(metaclass=MutationMetaclass):
    pass
