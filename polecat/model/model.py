from polecat.utils import to_list

from .exceptions import InvalidFieldError
from .omit import NONE
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
    @classmethod
    def db_name(self):
        # TODO: This is the worst.
        from polecat.project.project import get_active_project
        # TODO: Plus, this whole thing is duplicated from "db". I need
        # to be able to map from these declarative roles to the DB
        # ones. Probably just create the DB one during preparation?
        name = ''
        project = get_active_project()
        if project:
            name += project.name
        if self.Meta.app:
            name += self.Meta.app.name
        if name:
            name += '_'
        name += self.Meta.role
        return name


class Access(metaclass=AccessMetaclass):
    pass


class Query(metaclass=QueryMetaclass):
    pass


class Mutation(metaclass=MutationMetaclass):
    def resolve(self, context):
        raise NotImplementedError
