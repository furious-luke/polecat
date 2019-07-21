from functools import partial

from cached_property import cached_property

from polecat.utils import to_list

from .db.query import Q


class ResolverContext:
    def __init__(self, event=None):
        self.event = event

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


class ResolverChain:
    def __init__(self, resolvers=None):
        self.resolvers = []
        self.use(resolvers)

    def __call__(self, context, *args, **kwargs):
        return self.resolve(context, *args, **kwargs)

    def use(self, resolvers):
        resolvers = to_list(resolvers)
        for resolver in resolvers:
            resolver.set_chain(self)
        self.resolvers = resolvers + self.resolvers

    def resolve(self, context, *args, **kwargs):
        iterator = iter(ResolverIterator(self, context))
        return next(iterator)(*args, **kwargs)

    def chain_method(self, method_name, context, *args, **kwargs):
        iterator = iter(ResolverMethodIterator(self, context, method_name))
        return next(iterator)(*args, **kwargs)


class ResolverIterator:
    def __init__(self, chain, context):
        self.chain = chain
        self.context = context

    def __iter__(self):
        self.resolver_iter = iter(self.chain.resolvers)
        return self

    def __next__(self):
        resolver = next(self.resolver_iter)
        return partial(resolver, self.context, iterator=self)


class ResolverMethodIterator(ResolverIterator):
    def __init__(self, chain, context, method_name):
        super().__init__(chain, context)
        self.method_name = method_name

    def __next__(self):
        while True:
            resolver = next(self.resolver_iter)
            if hasattr(resolver, self.method_name):
                break
        return partial(getattr(resolver, self.method_name), self.context, iterator=self)


class Resolver:
    def __init__(self, chain=None):
        self.chain = chain

    def __call__(self, context, *args, **kwargs):
        return self.resolve(context, *args, **kwargs)

    def set_chain(self, chain):
        self.chain = chain

    def resolve(self, context, iterator, *args, **kwargs):
        return next(iterator)(*args, **kwargs)

    def chain_method(self, method_name, *args, **kwargs):
        return self.chain.chain_method(method_name, *args, **kwargs)


class QueryResolver(Resolver):
    def resolve(self, context, query=None):
        query = self.chain_method('build_query', context, query)
        results = self.chain_method('build_results', query)
        return results

    def build_query(self, context, query=None, **kwargs):
        if not query:
            query = Q(context.model_class)
        return query


class AllResolver(QueryResolver):
    def build_query(self, context, query=None, **kwargs):
        query = super().build_query(context, query)
        return query.select(context.selector)

    def build_results(self, context, query, **kwargs):
        return list(query)


class GetResolver(QueryResolver):
    def build_query(self, context, query=None, **kwargs):
        query = super().build_query(context, query)
        id = context.parse_argument('id')
        return (
            query
            .select(context.selector)
            .filter(id=id)
        )

    def build_results(self, context, query, **kwargs):
        return query.get()


class MutationResolver(Resolver):
    def resolve(self, context, **kwargs):
        model = self.chain_method('build_model', context)
        query = self.chain_method('build_query', context, model)
        query = self.chain_method('select_query', context, query)
        results = self.chain_method('build_results', context, query)
        return results

    def select_query(self, context, query, **kwargs):
        return (
            query
            .select(context.selector)
        )

    def build_results(self, context, query, **kwargs):
        return query.get()


class CreateResolver(MutationResolver):
    def build_model(self, context, **kwargs):
        model_class = context.model_class
        input = context.parse_input()
        return model_class(**input.change)

    def build_query(self, context, model, **kwargs):
        return Q(model).insert()


class UpdateResolver(CreateResolver):
    def build_model(self, context, **kwargs):
        model_class = context.model_class
        input = context.parse_input()
        context._id = context.parse_argument('id')
        return model_class(id=context._id, **input.change)

    def build_query(self, context, model, **kwargs):
        return Q(model).update()


class UpdateOrCreateResolver(CreateResolver):
    def build_model(self, context, **kwargs):
        model_class = context.model_class
        input = context.parse_input()
        context._id = context.parse_argument('id')
        if context._id is not None:
            model = model_class(id=context._id, **input.change)
        else:
            model = model_class(**input.change)
        return model

    def build_query(self, context, model, **kwargs):
        if context._id is not None:
            query = Q(model).update()
        else:
            query = Q(model).insert()
        return query
