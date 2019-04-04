import inspect
from functools import partial

from graphql.type import (GraphQLField, GraphQLInputObjectType, GraphQLList,
                          GraphQLObjectType, GraphQLSchema)

from ..model import Model, model_registry, mutation_registry, type_registry
from ..utils import add_attribute, uncapitalize
from .field import *  # noqa
from .registry import (add_graphql_type, graphql_field_registry,
                       graphql_type_registry)
from .resolve import resolve_all_query, resolve_mutation


def make_graphql_schema():
    graphql_types = []
    queries = {}
    mutations = {}
    for model in iter_valid_models():
        is_input = getattr(model.Meta, 'input', False)
        object_type_class = (
            GraphQLInputObjectType
            if is_input
            else GraphQLObjectType
        )
        # TODO: Description?
        graphql_type = add_attribute(object_type_class(
            name=model.Meta.name,
            fields=partial(make_all_object_fields, model, is_input)
        ), '_model', model)
        add_graphql_type(model, graphql_type)
        graphql_types.append(graphql_type)
        if issubclass(model, Model):
            queries.update(make_graphql_queries(model, graphql_type))
            mutations.update(make_graphql_mutations(model, graphql_type))
    for mutation in iter_valid_mutations():
        mutations.update(make_graphql_mutation(mutation))
    return GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields=queries
        ),
        mutation=GraphQLObjectType(
            name='Mutation',
            fields=mutations
        ) if mutations else None,
        types=graphql_types
    )


def iter_valid_models():
    for type in type_registry:
        # TODO: Skip any set to be ignored.
        yield type
    for model in model_registry:
        # TODO: Skip any set to be ignored.
        yield model


def iter_valid_mutations():
    for mutation in mutation_registry:
        yield mutation


def make_all_object_fields(model, input=False):
    return {
        name: make_object_field(model, field, input=input)
        for name, field in model.Meta.cc_fields.items()
    }


def make_object_field(model, field, input=False):
    for base_class in inspect.getmro(field.__class__):
        graphql_field = graphql_field_registry.get(base_class)
        if graphql_field:
            # TODO: Maybe remove the function call and do it in __init__?
            return graphql_field(model, field, input=input).make_graphql_field()
    raise Exception(f'unknown field type {field}')


def make_graphql_queries(model, graphql_type):
    # TODO: Add the model to the GraphQLField?
    return {
        make_all_query_inflection(model): GraphQLField(
            GraphQLList(graphql_type),
            resolve=resolve_all_query
        )
    }


def make_graphql_mutations(model, graphql_type):
    return {}


def make_all_query_inflection(model):
    return f'all{model.Meta.plural.capitalize()}'


def make_graphql_mutation(mutation):
    return {
        make_mutation_inflection(mutation): add_attribute(
            GraphQLField(
                graphql_type_registry[mutation.returns],
                {
                    'input': graphql_type_registry[mutation.input]
                } if mutation.input else None,
                resolve_mutation
            ), '_mutation', mutation()  # TODO: Don't actually need to instantiate here.
        )
    }


def make_mutation_inflection(mutation):
    return uncapitalize(mutation.Meta.name)
