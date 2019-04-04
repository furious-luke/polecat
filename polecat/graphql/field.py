from graphql.type import (GraphQLArgument, GraphQLEnumType, GraphQLEnumValue,
                          GraphQLField, GraphQLInputField, GraphQLInt,
                          GraphQLInterfaceType, GraphQLList, GraphQLNonNull,
                          GraphQLObjectType, GraphQLSchema, GraphQLString)

from ..model import field
from ..utils import add_attribute
from .registry import FieldMetaclass, graphql_type_registry

__all__ = ('Field', 'StringField', 'IntField', 'RelatedField')


class Field(metaclass=FieldMetaclass):
    graphql_type = None
    sources = ()

    def __init__(self, model, model_field, input=False):
        self.model = model
        self.model_field = model_field
        self.input = input

    def make_graphql_field(self):
        # TODO: Clean this up a bit.
        if self.input:
            self.graphql_field = add_attribute(
                GraphQLInputField(
                    self.get_graphql_type(),
                    description=self.get_description()
                ), '_field', self
            )
        else:
            self.graphql_field = add_attribute(
                GraphQLField(
                    self.get_graphql_type(),
                    resolve=self.get_resolver(),
                    description=self.get_description()
                ), '_field', self
            )
        return self.graphql_field

    def get_graphql_type(self):
        return self.graphql_type

    def get_resolver(self):
        return self.default_resolver

    def get_description(self):
        return ''

    def default_resolver(self, obj, path):
        return obj[self.model_field.name]


class StringField(Field):
    graphql_type = GraphQLString
    sources = (field.TextField,)


class IntField(Field):
    graphql_type = GraphQLInt
    sources = (field.IntField,)


class RelatedField(Field):
    sources = (field.RelatedField,)

    def get_graphql_type(self):
        return graphql_type_registry[self.model_field.other]
