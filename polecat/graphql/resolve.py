from graphql.type import GraphQLList

from ..db.connection import cursor
from ..db.sql import Q, S
from ..utils.exceptions import traceback
from .field import RelatedField


def resolve_all_query(obj, info):
    # TODO: Remove this in production.
    with traceback():
        graphql_type = info.return_type.of_type
        query = build_all_query(graphql_type, info.field_nodes[0])
        # TODO: Ensure cursor is cached. Or at least connection.
        with cursor() as curs:
            sql = query.evaluate()
            curs.execute(*sql)
            return map(lambda x: x[0], curs.fetchall())


def resolve_get_query(obj, info, query=None):
    graphql_type = info.return_type
    query = build_all_query(graphql_type, info.field_nodes[0], query=query)
    query.is_get = True  # TODO: Must be a better way.
    # TODO: Should use execute above.
    return query.execute()


def build_all_query(graphql_type, node, query=None):
    model = graphql_type._model
    if not query:
        query = Q(model)
    return query.select(get_selector_from_node(graphql_type, node))


def get_selector_from_node(graphql_type, node):
    # TODO: I'd like this to be bundled up in the GraphQL type itself,
    # as in we should call "graphql_type.polecat_fields" to get our
    # type. This means altering the instantiated GQLType during schema
    # construction.
    if isinstance(graphql_type, GraphQLList):
        graphql_type = graphql_type.of_type
    fields = []
    lookups = {}
    for field_node in node.selection_set.selections:
        cc_field_name = field_node.name.value
        graphql_field = graphql_type.fields[cc_field_name]
        model_field = graphql_field._field.model_field
        if isinstance(graphql_field._field, RelatedField):
            lookups[model_field.name] = get_selector_from_node(
                graphql_field.type,
                field_node
            )
        else:
            fields.append(model_field.name)
    return S(*fields, **lookups)


def resolve_create_mutation(obj, info, **kwargs):
    graphql_field = info.parent_type.fields[info.field_name]
    model_class = graphql_field.type._model
    input = kwargs['input']
    model = model_class(**translate_input(model_class, input))
    query = Q(model).insert()
    return resolve_get_query(obj, info, query=query)


def resolve_update_mutation(obj, info, **kwargs):
    pass


def resolve_mutation(obj, info, **kwargs):
    graphql_field = info.parent_type.fields[info.field_name]
    mutation = graphql_field._mutation
    input = kwargs['input']
    return mutation.resolve(**input)


def translate_input(model, input):
    return {
        model.Meta.cc_fields[k].name: v
        for k, v in input.items()
    }
