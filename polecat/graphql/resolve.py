from graphql import GraphQLError
from graphql.type import GraphQLList
from polecat.model.db import Q, S

from ..utils.exceptions import traceback
from .field import RelatedField
from .input import Input


def resolve_all_query(obj, info):
    graphql_type = info.return_type.of_type
    options = info.context or {}
    query = build_all_query(graphql_type, info.field_nodes[0], options=options)
    return list(query)


def resolve_get_query(obj, info, query=None):
    graphql_type = info.return_type
    options = info.context or {}
    with traceback():
        query = build_all_query(graphql_type, info.field_nodes[0], query=query, options=options)
        # TODO: Should use execute above.
        return query.get()


def build_all_query(graphql_type, node, query=None, options=None):
    model = graphql_type._model
    if not query:
        query = Q(model, **(options or {}))
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
        try:
            graphql_field = graphql_type.fields[cc_field_name]
        except KeyError:
            raise GraphQLError(f'No field "{cc_field_name}" on type "{graphql_type}"')
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
    mutation = info.parent_type.fields[info.field_name]
    return_type = info.return_type
    input_type = mutation.args['input'].type
    model_class = return_type._model
    try:
        input = Input(input_type, kwargs['input'])
    except KeyError:
        raise Exception('Missing "input" argument')
    # Perform any deletes.
    # TODO: While these are all done together, I'd like to add them to
    # the insert below.
    queries = []
    for delete_class, ids in input.delete.items():
        options = info.context or {}
        queries.extend([
            Q(delete_class, **options)
            .filter(id=id)
            .delete()
            for id in ids
        ])
    if queries:
        Q.common(*queries).execute()
    model = model_class(**input.change)
    # TODO: We can optimise this operation for the case where there
    # are no nested insertions like this...
    query = Q(model).insert()
    return resolve_get_query(obj, info, query=query)


def resolve_update_mutation(obj, info, **kwargs):
    mutation = info.parent_type.fields[info.field_name]
    return_type = info.return_type
    input_type = mutation.args['input'].type
    model_class = return_type._model
    try:
        input = Input(input_type, kwargs['input'])
    except KeyError:
        raise Exception('Missing "input" argument')
    # Perform any deletes.
    # TODO: This can one day be merged together. Before then, I need
    # to create a CTE system that allows me to combine queries more
    # elegantly.
    queries = []
    for delete_class, ids in input.delete.items():
        options = info.context or {}
        queries.extend([
            Q(delete_class, **options)
            .filter(id=id)
            .delete()
            for id in ids
        ])
    if queries:
        Q.common(*queries).execute()
    model = model_class(**input.change)
    # TODO: We can optimise this operation for the case where there
    # are no nested insertions like this...
    # TODO: Delete...
    query = Q(model).update()
    return resolve_get_query(obj, info, query=query)


def resolve_delete_mutation(obj, info, **kwargs):
    return_type = info.return_type
    id = kwargs['input']['id']
    model_class = return_type._model
    model = model_class(id=id)
    options = info.context or {}
    Q(model).delete().execute(**options)
    return {
        'id': id
    }


def resolve_query(obj, info, **kwargs):
    graphql_field = info.parent_type.fields[info.field_name]
    query = graphql_field._query
    # TODO: Need to pass the context.
    return query.resolve(**kwargs)


def resolve_mutation(obj, info, **kwargs):
    node = info.field_nodes[0]
    graphql_field = info.parent_type.fields[info.field_name]
    return_type = graphql_field.type
    options = info.context or {}
    mutation = graphql_field._mutation(
        selector=get_selector_from_node(return_type, node),
        **options
    )
    input = kwargs['input']
    return mutation.resolve(**input)
