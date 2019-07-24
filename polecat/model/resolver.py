import inspect
import logging
from functools import partial
from itertools import chain

from cached_property import cached_property

from polecat.utils import to_list

from .db.query import Q

logger = logging.getLogger(__name__)


class APIContext:
    def __init__(self, event=None):
        self.event = event
        self.stack = []

    def parse_argument(self, name):
        raise NotImplementedError

    def parse_input(self):
        raise NotImplementedError

    @cached_property
    def model_class(self):
        return self.get_model_class()

    def get_model_class(self):
        raise NotImplementedError

    @cached_property
    def selector(self):
        return self.get_selector()

    def get_selector(self):
        raise NotImplementedError


class ResolverContext:
    def __init__(self, manager, api_context):
        self.manager = manager
        self.api_context = api_context
        self.stack = []

    def __call__(self, *args, **kwargs):
        logger.debug('ResolveContext: moving to next operation')
        return next(self)(*args, **kwargs)

    def __next__(self):
        while len(self.stack):
            try:
                return next(self.stack[-1])
            except StopIteration:
                self.stack.pop()
                if not len(self.stack):
                    raise

    def __getattr__(self, key):
        return getattr(self.api_context, key)

    def push_iterator(self, iterator):
        self.stack.append(iterator)

    def cut_point(self, *args, **kwargs):
        return self.manager.cut_point(*args, **kwargs)


class ResolverList:
    def __init__(self, resolvers=None):
        self.resolvers = []
        self.use(resolvers)

    def __iter__(self):
        return iter(self.resolvers)

    def use(self, resolvers):
        # TODO: Track origin of resolvers.
        resolvers = to_list(resolvers)
        self.resolvers = resolvers + self.resolvers


class ResolverManager:
    def __call__(self, api_context, *args, **kwargs):
        return self.resolve(api_context, *args, **kwargs)

    def resolve(self, api_context, *args, **kwargs):
        logger.debug(f'Resolve: {self.__class__.__name__}')
        context = ResolverContext(self, api_context)
        return self.resolve_with_context(context, *args, **kwargs)

    def resolve_with_context(self, context, *args, **kwargs):
        iterator = iter(ResolverIterator(context))
        return next(iterator)(*args, **kwargs)

    def cut_point(self, method_name, context, *args, **kwargs):
        iterator = iter(ResolverMethodIterator(context, method_name))
        return next(iterator)(*args, **kwargs)

    def iter_resolvers(self, context):
        raise NotImplementedError


class CreateResolverManager(ResolverManager):
    def iter_resolvers(self, context):
        model_class = context.model_class
        return chain(
            model_class.Meta.mutation_resolvers,
            model_class.Meta.create_resolvers
        )


class UpdateResolverManager(ResolverManager):
    def iter_resolvers(self, context):
        model_class = context.model_class
        return chain(
            model_class.Meta.mutation_resolvers,
            model_class.Meta.update_resolvers
        )


class UpdateOrCreateResolverManager(ResolverManager):
    def resolve_with_context(self, context, *args, **kwargs):
        model_class = context.model_class
        input = context.parse_input()
        if input.change.get('id') is None:
            manager = model_class.Meta.create_resolver_manager
        else:
            manager = model_class.Meta.update_resolver_manager
        # TODO: Not too sure about this hard override of manager.
        context.manager = manager
        return manager.resolve_with_context(context, *args, **kwargs)


class ResolverIterator:
    def __init__(self, context):
        self.context = context
        self.context.push_iterator(self)

    def __iter__(self):
        logger.debug('ResolverIterator: initiating')
        self.resolver_iterator = self.context.manager.iter_resolvers(self.context)
        return self

    def __next__(self):
        logger.debug('ResolverIterator: moving to next resolver')
        while True:
            resolver = next(self.resolver_iterator)
            logger.debug(f'ResolverIterator: considering {resolver}')
            if hasattr(resolver, 'resolve'):
                logger.debug(f'ResolverIterator: accepting (has resolve method)')
                func = resolver.resolve
            elif not inspect.isclass(resolver) and callable(resolver):
                logger.debug(f'ResolverIterator: accepting (is callable)')
                func = resolver
            else:
                logger.debug(f'ResolverIterator: rejecting')
                continue
            return partial(func, self.context)


class ResolverMethodIterator(ResolverIterator):
    def __init__(self, context, method_name):
        super().__init__(context)
        self.method_name = method_name

    def __next__(self):
        while True:
            resolver = next(self.resolver_iterator)
            if not hasattr(resolver, self.method_name):
                continue
            return partial(getattr(resolver, self.method_name), self.context)


class QueryResolver:
    def resolve(self, context, query=None):
        query = context.cut_point('build_query', context, query)
        results = context.cut_point('build_results', query)
        return results

    def build_query(self, context, query=None):
        if not query:
            query = Q(context.model_class)
        return query


class AllResolver(QueryResolver):
    def build_query(self, context, query=None):
        query = super().build_query(context, query)
        return query.select(context.selector)

    def build_results(self, context, query):
        return list(query)


class GetResolver(QueryResolver):
    def build_query(self, context, query=None):
        query = super().build_query(context, query)
        id = context.parse_argument('id')
        return (
            query
            .select(context.selector)
            .filter(id=id)
        )

    def build_results(self, context, query):
        return query.get()


class MutationResolver:
    def resolve(self, context):
        model = context.cut_point('build_model', context)
        query = context.cut_point('build_query', context, model)
        query = context.cut_point('select_query', context, query)
        results = context.cut_point('build_results', context, query)
        return results

    def select_query(self, context, query):
        return (
            query
            .select(context.selector)
        )

    def build_results(self, context, query):
        return query.get()


class CreateResolver(MutationResolver):
    def build_model(self, context):
        model_class = context.model_class
        input = context.parse_input()
        return model_class(**input.change)

    def build_query(self, context, model):
        return Q(model).insert()


class UpdateResolver(CreateResolver):
    def build_model(self, context):
        model_class = context.model_class
        input = context.parse_input()
        context._id = context.parse_argument('id')
        return model_class(id=context._id, **input.change)

    def build_query(self, context, model):
        return Q(model).update()


# class UpdateOrCreateResolver(CreateResolver):
#     def build_model(self, context):
#         model_class = context.model_class
#         input = context.parse_input()
#         context._id = context.parse_argument('id')
#         if context._id is not None:
#             model = model_class(id=context._id, **input.change)
#         else:
#             model = model_class(**input.change)
#         return model

#     def build_query(self, context, model):
#         if context._id is not None:
#             query = Q(model).update()
#         else:
#             query = Q(model).insert()
#         return query
