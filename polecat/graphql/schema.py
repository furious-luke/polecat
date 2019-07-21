import inspect
import logging
from functools import partial

from graphql.type import (GraphQLField, GraphQLInputField,
                          GraphQLInputObjectType, GraphQLInt, GraphQLList,
                          GraphQLNonNull, GraphQLObjectType, GraphQLSchema,
                          GraphQLString)

from ..core.context import active_context
from ..model import (Model, model_registry, mutation_registry, omit,
                     query_registry)
from ..utils import add_attribute, capitalize, uncapitalize
from ..utils.stringcase import camelcase
# from .field import *  # noqa
from .registry import (add_graphql_create_input, add_graphql_type,
                       add_graphql_update_input, graphql_create_input_registry,
                       graphql_field_registry, graphql_reverse_input_registry,
                       graphql_type_registry, graphql_update_input_registry)
from .resolve import (resolve_all_query, resolve_create_mutation,
                      resolve_delete_mutation, resolve_get_query,
                      resolve_mutation, resolve_query, resolve_update_mutation,
                      resolve_update_or_create_mutation)
from .type import scalars

logger = logging.getLogger(__name__)


def build_graphql_schema():
    # TODO: I need to fix this nonsense. The registries need to be
    # first-class citizens that can be cleared when needed.
    global graphql_create_input_registry
    global graphql_update_input_registry
    global graphql_reverse_input_registry
    all_keys = list(graphql_create_input_registry.keys())
    for k in all_keys:
        del graphql_create_input_registry[k]
    all_keys = list(graphql_update_input_registry.keys())
    for k in all_keys:
        del graphql_update_input_registry[k]
    all_keys = list(graphql_reverse_input_registry.keys())
    for k in all_keys:
        del graphql_reverse_input_registry[k]
    return SchemaBuilder().build()


# TODO: Make the builders class only?
class SchemaBuilder:
    def build(self):
        logger.debug('Building GraphQL schema')
        self.types = []
        self.queries = {}
        self.mutations = {}
        self.build_models()
        self.build_queries()
        self.build_mutations()
        return GraphQLSchema(
            query=GraphQLObjectType(
                name='Query',
                fields=self.queries
            ),
            mutation=GraphQLObjectType(
                name='Mutation',
                fields=self.mutations
            ) if self.mutations else None,
            types=scalars + self.types
        )

    # TODO: Should have called this "delete_input_type".
    @property
    def delete_type(self):
        return self.build_delete_type()

    @property
    def delete_output_type(self):
        return self.build_delete_output_type()

    def build_models(self):
        logger.debug('Building GraphQL models')
        builders = []
        for model in self.iter_models():
            builder_class = getattr(model.Meta, 'builder', ModelBuilder)
            builder = builder_class(self)
            builder.build(model)
            builders.append(builder)
        for builder in builders:
            builder.post_build(self)

    def build_queries(self):
        logger.debug('Building GraphQL queries')
        for query in self.iter_queries():
            builder_class = getattr(query, 'builder', QueryBuilder)
            builder = builder_class(self)
            builder.build(query)

    def build_mutations(self):
        logger.debug('Building GraphQL mutations')
        for mutation in self.iter_mutations():
            builder_class = getattr(mutation, 'builder', MutationBuilder)
            builder = builder_class(self)
            builder.build(mutation)

    @active_context
    def iter_models(self, context=None):
        for type in context.registries.type_registry:
            if not type.Meta.omit == omit.ALL:
                yield type
        for model in model_registry:
            if not model.Meta.omit == omit.ALL:
                yield model

    def iter_queries(self):
        for query in query_registry:
            yield query

    def iter_mutations(self):
        for mutation in mutation_registry:
            yield mutation

    def build_delete_type(self):
        # TODO: Use a function cache.
        type = getattr(self, '_delete_type', None)
        if not type:
            type = GraphQLInputObjectType(
                name='DeleteByIDInput',
                fields={
                    'id': GraphQLInputField(GraphQLInt)
                }
            )
            self._delete_type = type
        return type

    def build_delete_output_type(self):
        # TODO: Use a function cache.
        type = getattr(self, '_delete_output_type', None)
        if not type:
            type = GraphQLObjectType(
                name='DeleteByID',
                fields={
                    'id': GraphQLField(GraphQLInt)
                }
            )
            self._delete_output_type = type
        return type


class ModelBuilder:
    def __init__(self, schema_builder):
        self.schema_builder = schema_builder

    def build(self, model):
        self.model = model
        self.type = self.build_type(model)
        self.schema_builder.types.append(self.type)

    # TODO: Can remove `schema_builder`?
    def post_build(self, schema_builder):
        if issubclass(self.model, Model):
            schema_builder.queries.update(self.build_queries(self.model, self.type))
            schema_builder.mutations.update(self.build_mutations(self.model, self.type))

    def build_type(self, model):
        if getattr(model.Meta, 'input', False):
            return InputBuilder(self.schema_builder).build(model)
        else:
            return TypeBuilder(self.schema_builder).build(model)

    def build_queries(self, model, type):
        # TODO: Add the model to the GraphQLField?
        return {
            **self.build_all_queries(model, type),
            **self.build_get_queries(model, type)
        }

    def build_mutations(self, model, type):
        mutations = {}
        if not model.Meta.omit & omit.CREATE:
            args = {}
            create_input = CreateInputBuilder(self.schema_builder).build(model)
            if create_input:
                args['input'] = create_input
            mutations[self.create_mutation_inflection(model)] = GraphQLField(
                type,
                args,
                resolve_create_mutation
            )
        if not model.Meta.omit & omit.UPDATE:
            args = {
                'id': GraphQLNonNull(GraphQLInt)
            }
            update_input = UpdateInputBuilder(self.schema_builder).build(model)
            if update_input:
                args['input'] = update_input
            mutations[self.update_mutation_inflection(model)] = GraphQLField(
                type,
                args,
                resolve_update_mutation
            )
        if not model.Meta.omit & omit.UPDATE and not model.Meta.omit & omit.CREATE:
            args = {
                'id': GraphQLInt
            }
            if update_input:
                args['input'] = update_input
            mutations[self.update_or_create_mutation_inflection(model)] = GraphQLField(
                type,
                args,
                resolve_update_or_create_mutation
            )
        if not model.Meta.omit & omit.DELETE:
            # TODO: Need to use type instead of delete_output_type
            # because it contains details about the model class
            # used. Will need to think about how to handle situations
            # where a type is shared amongst numerous models.
            mutations[self.delete_mutation_inflection(model)] = GraphQLField(
                type,
                {
                    'input': DeleteInputBuilder(self.schema_builder).build(model)
                },
                resolve_delete_mutation
            )
        return mutations

    def build_all_queries(self, model, type):
        queries = {}
        if not model.Meta.omit & omit.LIST:
            queries[self.all_query_inflection(model)] = GraphQLField(
                GraphQLList(type),
                resolve=resolve_all_query
            )
        return queries

    def build_get_queries(self, model, type):
        queries = {}
        if not model.Meta.omit & omit.GET:
            # TODO: Need to add some details to the field to support
            # getting by?
            for name, field in model.Meta.cc_fields.items():
                if field.omit & omit.GET:
                    continue
                if not field.use_get_query():
                    continue
                queries[self.get_query_inflection(model, field)] = add_attribute(
                    GraphQLField(
                        type,
                        {
                            # TODO: What happens when the type linked is
                            # something complicated, like a GraphQLObject?
                            # Will need to use the PK of the
                            # relationship. What if there's several?
                            name: type.fields[name].type
                        },
                        resolve=resolve_get_query
                    ),
                    '_type', type
                )
        return queries

    def all_query_inflection(self, model):
        # TODO: Not sure I need to capitalize?
        return f'all{model.Meta.plural}'

    def get_query_inflection(self, model, field):
        name = f'get{model.Meta.name}'
        if not field.primary_key:
            name += f'By{capitalize(field.cc_name)}'
        return name

    def create_mutation_inflection(self, model):
        return f'create{model.Meta.name}'

    def update_mutation_inflection(self, model):
        return f'update{model.Meta.name}'

    def update_or_create_mutation_inflection(self, model):
        return f'updateOrCreate{model.Meta.name}'

    def delete_mutation_inflection(self, model):
        return f'delete{model.Meta.name}'


class TypeBuilder:
    object_type_class = GraphQLObjectType

    def __init__(self, schema_builder):
        self.schema_builder = schema_builder

    def build(self, model):
        object_type_class = self.get_object_type_class()
        # TODO: Description?
        type = add_attribute(
            object_type_class(
                name=self.get_type_name(model),
                fields=partial(self.build_all_fields, model)
            ),
            '_model', model
        )
        # TODO: Current assumption is that there's just one gql type
        # per model. May need to alter this in the future. I'm not
        # storing any of the model create, update, etc inputs.
        self.register_type(model, type)
        return type

    def get_type_name(self, model):
        return model.Meta.name

    def build_all_fields(self, model):
        logger.debug(f'Building GraphQL fields for model {model.Meta.name} using builder {self.__class__.__name__}')
        # TODO: Can I make this more functional?
        fields = {}
        for name, field in self.iter_fields(model):
            result = self.build_field(model, field)
            if isinstance(result, dict):
                fields.update(result)
            elif result is None:
                pass
            else:
                fields[name] = result
        return fields

    def build_field(self, model, field):
        for base_class in inspect.getmro(field.__class__):
            my_graphql_field = graphql_field_registry.get(base_class)
            # TODO: Nomenclature mishap here. Need a name for my
            # GraphQL type abstraction that doesn't clash with actual
            # graphql types.
            if my_graphql_field:
                logger.debug(f'Building field {field.cc_name}')
                field = self.get_graphql_field(model, field, my_graphql_field)
                logger.debug('DONE')
                return field
        raise Exception(f'unknown field type {field}')

    def get_graphql_field(self, model, field, my_graphql_field):
        # TODO: Maybe remove the function call and do it in __init__?
        return my_graphql_field(model, field).make_graphql_field(self.schema_builder)

    def get_object_type_class(self):
        return self.object_type_class

    def register_type(self, model, type):
        add_graphql_type(model, type)

    def iter_fields(self, model):
        for name, field in model.Meta.cc_fields.items():
            if field.omit & (omit.LIST | omit.GET):
                continue
            yield name, field


class InputBuilder(TypeBuilder):
    object_type_class = GraphQLInputObjectType

    def get_type_name(self, model):
        # TODO: Probably shouldn't need this conditional.
        name = model.Meta.name
        if name[-5:] != 'Input':
            name += 'Input'
        return name

    def get_graphql_field(self, model, field, my_graphql_field):
        # TODO: Maybe remove the function call and do it in __init__?
        return my_graphql_field(model, field, input=True).make_graphql_field(self.schema_builder)

    def iter_fields(self, model):
        for name, field in model.Meta.cc_fields.items():
            yield name, field


class CreateInputBuilder(InputBuilder):
    def get_type_name(self, model):
        return f'{model.Meta.name}CreateInput'

    def get_graphql_field(self, model, field, my_graphql_field):
        # TODO: Maybe remove the function call and do it in __init__?
        # TODO: Have to pass in a type because reverse fields generate
        # a new object-type internally instead of just a type, so it
        # needs a name. So, if I don't pass in a type string create,
        # update, delete will produce identically named object-types.
        return my_graphql_field(
            model,
            field,
            input=True,
            registry=graphql_create_input_registry  # TODO: Yuck
        ).make_graphql_field(self.schema_builder)

    def register_type(self, model, type):
        add_graphql_create_input(model, type)

    def iter_fields(self, model):
        for name, field in model.Meta.cc_fields.items():
            if field.omit & omit.CREATE:
                continue
            yield name, field


class UpdateInputBuilder(InputBuilder):
    def get_type_name(self, model):
        return f'{model.Meta.name}UpdateInput'

    def get_graphql_field(self, model, field, my_graphql_field):
        # TODO: Maybe remove the function call and do it in __init__?
        # TODO: Check if it's not the ID field used for the update,
        # and if not, make the field optional.
        # TODO: Have to pass in a type because reverse fields generate
        # a new object-type internally instead of just a type, so it
        # needs a name. So, if I don't pass in a type string create,
        # update, delete will produce identically named object-types.
        return my_graphql_field(
            model,
            field,
            input=True,
            registry=graphql_update_input_registry  # TODO: Yuck
        ).make_graphql_field(self.schema_builder)

    def register_type(self, model, type):
        add_graphql_update_input(model, type)

    def iter_fields(self, model):
        for name, field in model.Meta.cc_fields.items():
            if field.omit & omit.UPDATE:
                continue
            if name == 'id':
                continue
            yield name, field


class DeleteInputBuilder(InputBuilder):
    def build(self, model):
        object_type_class = self.get_object_type_class()
        # TODO: Description?
        type = add_attribute(
            object_type_class(
                name=self.get_type_name(model),
                fields={
                    'id': GraphQLInt
                }
            ),
            '_model', model
        )
        # TODO: Current assumption is that there's just one gql type
        # per model. May need to alter this in the future. I'm not
        # storing any of the model create, update, etc inputs.
        # self.register_type(model, type)
        return type

    def get_type_name(self, model):
        return f'{model.Meta.name}DeleteInput'

    def iter_fields(self, model):
        for name, field in model.Meta.cc_fields.items():
            if field.omit & omit.DELETE:
                continue
            yield name, field


class ReverseModelInputBuilder(InputBuilder):
    def build(self, model, source_field):
        # TODO: Do I need to pass source_field around, or okay to
        # store on the builder?
        self.source_field = source_field
        logger.debug(f'Building GraphQL reverse model input {self.get_type_name(model)}')
        return super().build(model)

    def get_graphql_field(self, model, field, my_graphql_field):
        # TODO: Maybe remove the function call and do it in __init__?
        # TODO: Check if it's not the ID field used for the update,
        # and if not, make the field optional.
        # TODO: Have to pass in a type because reverse fields generate
        # a new object-type internally instead of just a type, so it
        # needs a name. So, if I don't pass in a type string create,
        # update, delete will produce identically named object-types.
        return my_graphql_field(
            model,
            field,
            input=True,
            registry=graphql_create_input_registry  # TODO: Yuck
        ).make_graphql_field(self.schema_builder)

    def get_type_name(self, model):
        return f'{model.Meta.name}{capitalize(self.source_field.cc_name)}ReverseInput'

    def iter_fields(self, model):
        for name, field in model.Meta.cc_fields.items():
            if field != self.source_field:
                yield name, field


class QueryBuilder:
    def __init__(self, schema_builder):
        self.schema_builder = schema_builder

    def build(self, query):
        self.schema_builder.queries.update(self.build_queries(query))

    def build_queries(self, query):
        queries = {}
        if not query.Meta.omit & omit.ALL:
            queries[self.query_inflection(query)] = add_attribute(
                GraphQLField(
                    self.build_return_type(query),
                    self.build_arguments(query),
                    resolve_query
                ),
                '_query', query()  # TODO: Don't actually need to instantiate here.
            )
        return queries

    def build_return_type(self, query):
        if isinstance(query.returns, list):
            return GraphQLList(graphql_type_registry[query.returns[0]])
        else:
            return graphql_type_registry[query.returns]

    def build_arguments(self, query):
        args = {}
        for name, type in getattr(query, 'arguments', ()):
            # TODO: This should be looking up from a table.
            args[camelcase(name)] = self.map_type(type)
        return args

    def map_type(self, type):
        if type == str:
            return GraphQLString
        elif type == int:
            return GraphQLInt
        else:
            raise NotImplementedError(f'invalid GraphQL argument: {type}')
                

    def query_inflection(self, query):
        return uncapitalize(query.Meta.name)


class MutationBuilder:
    def __init__(self, schema_builder):
        self.schema_builder = schema_builder

    def build(self, mutation):
        self.schema_builder.mutations.update(self.build_mutations(mutation))

    def build_mutations(self, mutation):
        mutations = {}
        if not mutation.Meta.omit & omit.ALL:
            mutations[self.mutation_inflection(mutation)] = add_attribute(
                GraphQLField(
                    graphql_type_registry[mutation.returns],
                    {
                        'input': graphql_type_registry[mutation.input]
                    } if mutation.input else None,
                    resolve_mutation
                ),
                '_mutation', mutation
            )
        return mutations

    def mutation_inflection(self, mutation):
        return uncapitalize(mutation.Meta.name)
