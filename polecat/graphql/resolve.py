from graphql import GraphQLError
from graphql.type import GraphQLList
from polecat.model.db import Q, S

from ..utils.exceptions import traceback
from .field import RelatedField
from .input import Input, parse_id


class Resolver:
    @classmethod
    def as_function(cls, *args, **kwargs):
        return cls(*args, **kwargs).resolve()

    def __init__(self, root, info, **kwargs):
        self.root = root
        self.info = info
        self.kwargs = kwargs

    def resolve(self):
        raise NotImplementedError

    def parse_input(self):
        try:
            return Input(self.input_type, self.kwargs['input'])
        except KeyError:
            raise Exception('Missing "input" argument')

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
    def context(self):
        return self.info.context

    @property
    def polecat_model_class(self):
        return self.return_type._model

    @property
    def input_type(self):
        return self.field.args['input'].type

    def parse_id(self):
        try:
            id = parse_id(self.kwargs['id'])
        except KeyError:
            id = None
        return id


class CreateResolver(Resolver):
    def resolve(self):
        model_class = self.polecat_model_class
        model = self.build_model(model_class)
        custom_resolver = model_class.Meta.mutation_resolver
        if custom_resolver:
            return custom_resolver(model, self.complete_resolve)
        else:
            return self.complete_resolve(model)

    def build_model(self, model_class):
        input = self.parse_input()
        return model_class(**input.change)

    def complete_resolve(self, model):
        query = self.build_query(model)
        return resolve_get_query(self.root, self.info, query=query)

    def build_query(self, model):
        return Q(model).insert()


class UpdateResolver(CreateResolver):
    def build_model(self, model_class):
        input = self.parse_input()
        self._id = self.parse_id()
        model = model_class(id=self._id, **input.change)
        return model

    def build_query(self, model):
        return Q(model).update()


class UpdateOrCreateResolver(CreateResolver):
    def build_model(self, model_class):
        input = self.parse_input()
        self._id = self.parse_id()
        if self._id is not None:
            model = model_class(id=self._id, **input.change)
        else:
            model = model_class(**input.change)
        return model

    def build_query(self, model):
        if self._id is not None:
            query = Q(model).update()
        else:
            query = Q(model).insert()
        return query


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


# def resolve_create_mutation(obj, info, **kwargs):
#     mutation = info.parent_type.fields[info.field_name]
#     return_type = info.return_type
#     input_type = mutation.args['input'].type
#     model_class = return_type._model
#     try:
#         input = Input(input_type, kwargs['input'])
#     except KeyError:
#         raise Exception('Missing "input" argument')
#     # Perform any deletes.
#     # TODO: While these are all done together, I'd like to add them to
#     # the insert below.
#     queries = []
#     for delete_class, ids in input.delete.items():
#         options = info.context or {}
#         queries.extend([
#             Q(delete_class, **options)
#             .filter(id=id)
#             .delete()
#             for id in ids
#         ])
#     if queries:
#         Q.common(*queries).execute()
#     model = model_class(**input.change)
#     # TODO: We can optimise this operation for the case where there
#     # are no nested insertions like this...
#     query = Q(model).insert()
#     return resolve_get_query(obj, info, query=query)


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
    model = model_class(id=parse_id(kwargs['id']), **input.change)
    # TODO: We can optimise this operation for the case where there
    # are no nested insertions like this...
    # TODO: Delete...
    query = Q(model).update()
    return resolve_get_query(obj, info, query=query)


# def resolve_update_or_create_mutation(obj, info, **kwargs):
#     mutation = info.parent_type.fields[info.field_name]
#     return_type = info.return_type
#     input_type = mutation.args['input'].type
#     model_class = return_type._model
#     try:
#         input = Input(input_type, kwargs['input'])
#     except KeyError:
#         raise Exception('Missing "input" argument')
#     # Perform any deletes.
#     # TODO: This can one day be merged together. Before then, I need
#     # to create a CTE system that allows me to combine queries more
#     # elegantly.
#     queries = []
#     for delete_class, ids in input.delete.items():
#         options = info.context or {}
#         queries.extend([
#             Q(delete_class, **options)
#             .filter(id=id)
#             .delete()
#             for id in ids
#         ])
#     if queries:
#         Q.common(*queries).execute()
#     try:
#         id = parse_id(kwargs['id'])
#     except KeyError:
#         id = None
#     # TODO: We can optimise this operation for the case where there
#     # are no nested insertions like this...
#     # TODO: Delete...
#     if id is not None:
#         model = model_class(id=id, **input.change)
#         query = Q(model).update()
#     else:
#         model = model_class(**input.change)
#         query = Q(model).insert()
#     return resolve_get_query(obj, info, query=query)


def resolve_delete_mutation(obj, info, **kwargs):
    return_type = info.return_type
    id = parse_id(kwargs['input']['id'])
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
