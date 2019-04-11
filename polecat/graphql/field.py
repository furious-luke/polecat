from graphql.type import (GraphQLArgument, GraphQLBoolean, GraphQLEnumType,
                          GraphQLEnumValue, GraphQLField, GraphQLFloat,
                          GraphQLInputField, GraphQLInputObjectType,
                          GraphQLInt, GraphQLInterfaceType, GraphQLList,
                          GraphQLNonNull, GraphQLObjectType, GraphQLSchema,
                          GraphQLString)

from ..model import field
from ..utils import add_attribute, capitalize
from .registry import (FieldMetaclass, graphql_create_input_registry,
                       graphql_reverse_input_registry, graphql_type_registry,
                       graphql_update_input_registry)
from .type import GraphQLDatetime

__all__ = ('Field', 'StringField', 'IntField', 'RelatedField')


class Field(metaclass=FieldMetaclass):
    graphql_type = None
    sources = ()

    def __init__(self, model, model_field, input=False, registry=None):
        self.model = model
        self.model_field = model_field
        self.input = input
        self.registry = registry or graphql_type_registry

    def make_graphql_field(self, name=None, optional=False):
        # TODO: Clean this up a bit.
        if self.input:
            # TODO: Use `optional` to remove required attributes. Used
            # for patches.
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

    def from_input(self, input):
        result = {}
        name = self.model_field.cc_name
        if name in input:
            result[self.model_field.name] = input[name]
        return result


class StringField(Field):
    graphql_type = GraphQLString
    sources = (field.TextField,)


class DatetimeField(Field):
    graphql_type = GraphQLDatetime
    sources = (field.DatetimeField,)


class BoolField(Field):
    graphql_type = GraphQLBoolean
    sources = (field.BoolField,)


class IntField(Field):
    graphql_type = GraphQLInt
    sources = (field.IntField,)


class FloatField(Field):
    graphql_type = GraphQLFloat
    sources = (field.FloatField,)


class RelatedField(Field):
    sources = (field.RelatedField,)

    def get_graphql_type(self, registry=None):
        registry = registry or self.registry
        return registry[self.model_field.other]


class ReverseField(RelatedField):
    sources = (field.ReverseField,)

    def make_graphql_field(self, builder):
        if self.input:
            name = f'{self.model_field.other.Meta.name}ReverseInput'
            type = graphql_reverse_input_registry.get(name, None)
            if not type:
                # TODO: Noooooooo. Use the buidler getting passed in
                # to provide it.
                from .schema import ReverseModelInputBuilder
                type = add_attribute(
                    GraphQLInputObjectType(
                        name=name,
                        fields={
                            'create': GraphQLList(
                                ReverseModelInputBuilder(builder).build(
                                    self.model_field.other,
                                    self.model_field.other.Meta.fields[self.model_field.related_name]
                                )
                            ),
                            'delete': GraphQLList(builder.delete_type)
                        }
                    ), '_model', self.model
                )
                graphql_reverse_input_registry[name] = type
            return type
        else:
            return super().make_graphql_field()

    def get_graphql_type(self, registry=None):
        return GraphQLList(super().get_graphql_type(registry))
