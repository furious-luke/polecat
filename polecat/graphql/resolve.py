from graphql import GraphQLError
from graphql.type import GraphQLList
from polecat.model.db import Q, S
from polecat.model.resolver import APIContext

from ..utils.exceptions import traceback
from .field import RelatedField
from .input import Input, parse_id


class GraphQLAPIContext(APIContext):
    def __init__(self, root, info, **kwargs):
        super().__init__()
        self.root = root
        self.info = info
        self.kwargs = kwargs
        self.session = self.graphql_context.get('session')

    def parse_argument(self, name):
        return self.kwargs.get(name)

    def parse_input(self):
        try:
            return Input(self.input_type, self.kwargs['input']).change
        except KeyError:
            raise Exception('Missing "input" argument')

    def raw_input(self):
        return self.kwargs['input']

    @property
    def field_name(self):
        return self.info.field_name

    @property
    def field(self):
        # TODO: Cache.
        return self.info.parent_type.fields[self.field_name]

    @property
    def return_type(self):
        return self.info.return_type

    @property
    def root_node(self):
        return self.info.field_nodes[0]

    @property
    def graphql_context(self):
        return self.info.context or {}

    @property
    def model_class(self):
        try:
            return self.return_type._model
        except AttributeError:
            return self.return_type.of_type._model

    @property
    def input_type(self):
        return self.field.args['input'].type

    def parse_id(self):
        try:
            id = parse_id(self.kwargs['id'])
        except KeyError:
            id = None
        return id

    def get_selector(self):
        return get_selector_from_node(self.return_type, self.root_node)


def resolve_all_query(obj, info, **kwargs):
    with traceback():
        ctx = GraphQLAPIContext(obj, info, **kwargs)
        return ctx.model_class.Meta.all_resolver_manager(ctx)


def resolve_get_query(obj, info, **kwargs):
    with traceback():
        ctx = GraphQLAPIContext(obj, info, **kwargs)
        return ctx.model_class.Meta.get_resolver_manager(ctx)


def resolve_create_mutation(obj, info, **kwargs):
    with traceback():
        ctx = GraphQLAPIContext(obj, info, **kwargs)
        return ctx.model_class.Meta.create_resolver_manager(ctx)


def resolve_update_mutation(obj, info, **kwargs):
    with traceback():
        ctx = GraphQLAPIContext(obj, info, **kwargs)
        return ctx.model_class.Meta.update_resolver_manager(ctx)


def resolve_update_or_create_mutation(obj, info, **kwargs):
    with traceback():
        ctx = GraphQLAPIContext(obj, info, **kwargs)
        return ctx.model_class.Meta.update_or_create_resolver_manager(ctx)


def resolve_delete_mutation(obj, info, **kwargs):
    with traceback():
        ctx = GraphQLAPIContext(obj, info, **kwargs)
        return ctx.model_class.Meta.delete_resolver_manager(ctx)
    # return_type = info.return_type
    # id = parse_id(kwargs['input']['id'])
    # model_class = return_type._model
    # model = model_class(id=id)
    # options = info.context or {}
    # Q(model).delete().execute(**options)
    # return {
    #     'id': id
    # }


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
