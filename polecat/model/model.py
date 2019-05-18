from .exceptions import InvalidFieldError
from .registry import (AccessMetaclass, ModelMetaclass, MutationMetaclass,
                       QueryMetaclass, RoleMetaclass, TypeMetaclass)


# TODO: Types and models are soooo similar, perhaps use a better
# architecture than total separation?
class Type(metaclass=TypeMetaclass):
    _registry = 'type_registry'
    _registry_base = 'Type'

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


class Access(metaclass=AccessMetaclass):
    pass


class Query(metaclass=QueryMetaclass):
    pass


class Mutation(metaclass=MutationMetaclass):
    pass
