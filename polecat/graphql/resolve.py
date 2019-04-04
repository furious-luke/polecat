from ..db.connection import cursor
from ..db.sql import Q, S
from .field import RelatedField


def resolve_all_query(obj, info):
    graphql_type = info.return_type.of_type
    query = build_query(graphql_type, info.field_nodes[0])
    # TODO: Ensure cursor is cached. Or at least connection.
    with cursor() as curs:
        sql = query.evaluate()
        curs.execute(*sql)
        return map(lambda x: x[0], curs.fetchall())


def build_query(graphql_type, node):
    model = graphql_type._model
    return Q(model).select(get_selector_from_node(graphql_type, node))


def get_selector_from_node(graphql_type, node):
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


def resolve_mutation(obj, info, **kwargs):
    graphql_field = info.parent_type.fields[info.field_name]
    mutation = graphql_field._mutation
    input = kwargs['input']
    return mutation.resolve(**input)
