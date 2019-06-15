import logging
from functools import partial

from graphql.type import (GraphQLArgument, GraphQLBoolean, GraphQLEnumType,
                          GraphQLEnumValue, GraphQLField, GraphQLFloat,
                          GraphQLInputField, GraphQLInputObjectType,
                          GraphQLInt, GraphQLInterfaceType, GraphQLList,
                          GraphQLNonNull, GraphQLObjectType, GraphQLSchema,
                          GraphQLString)

from ..model import field, omit
from ..utils import add_attribute, capitalize
from .input import Input
from .registry import (FieldMetaclass, graphql_create_input_registry,
                       graphql_reverse_input_registry, graphql_type_registry,
                       graphql_update_input_registry)
from .type import GraphQLDatetime, GraphQLUUID

__all__ = ('Field', 'StringField', 'IntField', 'RelatedField')

logger = logging.getLogger(__name__)


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

    def from_input(self, input, graphql_type):
        name = self.model_field.cc_name
        if name in input:
            change = {
                self.model_field.name: input[name]
            }
        else:
            change = None
        return change, None


class StringField(Field):
    graphql_type = GraphQLString
    sources = (field.TextField,)


class DatetimeField(Field):
    graphql_type = GraphQLDatetime
    sources = (field.DatetimeField,)


class UUIDField(Field):
    graphql_type = GraphQLUUID
    sources = (field.UUIDField,)


class PointField(Field):
    graphql_type = GraphQLList(GraphQLFloat)
    sources = (field.PointField,)


class BoolField(Field):
    graphql_type = GraphQLBoolean
    sources = (field.BoolField,)


class IntField(Field):
    graphql_type = GraphQLInt
    sources = (field.IntField,)


class SerialField(Field):
    graphql_type = GraphQLInt
    sources = (field.SerialField,)


class FloatField(Field):
    graphql_type = GraphQLFloat
    sources = (field.FloatField,)


class RelatedField(Field):
    sources = (field.RelatedField,)

    # TODO: Should maybe have an extra function to avoid even getting
    # here?  Like `should_build`?
    def make_graphql_field(self, name=None, optional=False):
        if self.model_field.other.Meta.omit == omit.ALL:
            return None
        else:
            return super().make_graphql_field(name, optional)

    def get_graphql_type(self, registry=None):
        registry = registry or self.registry
        try:
            return registry[self.model_field.other]
        except KeyError:
            raise KeyError(f'unknown GraphQL type {self.model_field.other.Meta.name}')

    def from_input(self, input, graphql_type):
        # TODO: Nesting.
        return super().from_input(input, graphql_type)


class ReverseField(RelatedField):
    sources = (field.ReverseField,)

    def make_graphql_field(self, builder):
        if self.input:
            name = f'{self.model.Meta.name}{capitalize(self.model_field.cc_name)}Input'
            type = graphql_reverse_input_registry.get(name, None)
            if not type:
                logger.debug(f'Building reverse input for model {name} coming from {self.model.Meta.name}.{self.model_field.name}')
                # TODO: Noooooooo. Use the buidler getting passed in
                # to provide it.
                type = add_attribute(
                    GraphQLInputObjectType(
                        name=name,
                        fields=partial(self.build_reverse_fields, builder)
                    ), '_model', self.model
                )
                graphql_reverse_input_registry[name] = type
            return add_attribute(
                GraphQLInputField(
                    type,
                    description=self.get_description()
                ), '_field', self
            )
        else:
            return super().make_graphql_field()

    def build_reverse_fields(self, builder):
        from .schema import ReverseModelInputBuilder
        return {
            'create': GraphQLList(
                ReverseModelInputBuilder(builder).build(
                    self.model_field.other,
                    self.model_field.other.Meta.fields[self.model_field.related_name]
                )
            ),
            'delete': GraphQLList(builder.delete_type)
        }

    def get_graphql_type(self, registry=None):
        return GraphQLList(super().get_graphql_type(registry))

    def from_input(self, input, graphql_type):
        name = self.model_field.cc_name
        if name in input:
            # TODO: Nesting.
            # TODO: Is this a bit inefficient? All the conditionls?
            delete = input[name].get('delete', set())
            change = input[name].get('create', None)
            if change:
                sub_type = graphql_type.fields[self.model_field.cc_name].type.fields['create'].type.of_type
                new_change = []
                for sub_args in change:
                    sub_input = Input(sub_type, sub_args)
                    sub_input.merge_delete(sub_input.delete, delete)
                    new_change.append(sub_input.change)
                change = {
                    self.model_field.name: new_change
                }
            if not len(delete):
                delete = None
        else:
            change, delete = None, None
        return change, delete
