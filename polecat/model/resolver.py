import inspect
from functools import partial

from cached_property import cached_property
from polecat.utils import to_list


class ResolverChain:
    def __init__(self):
        self.resolvers = []
        self.root_resolver = None
        self.chained_methods = {}

    def use(self, resolver):
        self.resolvers = to_list(resolver) + self.resolvers

    def prepare(self):
        self.prepare_root_resolver()
        self.prepare_chained_methods()

    def prepare_root_resolver(self):
        root_resolver = None
        for resolver in self.resolvers[::-1]:
            resolver = self.instantiate_resolver(resolver)
            root_resolver = partial(resolver, resolver=root_resolver)
        self.root_resolver = root_resolver

    def instantiate_resolver(self, resolver):
        if inspect.isclass(resolver):
            return resolver()
        else:
            return resolver

    def prepare_chained_methods(self):
        for ii, base_resolver in enumerate(self.resolver[::-1]):
            if not isinstance(base_resolver, Resolver):
                continue
            for method_name in base_resolver.chained_methods:
                root_method = None
                for resolver in self.resolver[:ii:-1]:
                    try:
                        root_method = partial(getattr(resolver, method_name), method=root_method)
                    except AttributeError:
                        pass
                self.chained_methods[method_name] = root_method

    def resolve(self, context):
        try:
            return self.root_resolver(context)
        except AttributeError:
            # TODO: Better error type.
            raise Exception('ResolverChain has not been prepared, or no resolvers used')

    def chain_method(self, method_name, *args, **kwargs):
        try:
            return self.chained_methods[method_name](*args, **kwargs)
        except KeyError:
            raise KeyError(f'Invalid chained method name: {method_name}')


class ResolverContext:
    def __init__(self, event=None):
        self.event = event

    @cached_property
    def model(self):
        # TODO: Cache.
        raise NotImplementedError

    @cached_property
    def query(self):
        # TODO: Cache.
        raise NotImplementedError


class Resolver:
    @classmethod
    def factory(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __init__(self, root, info, **kwargs):
        super().__init__()
        self.root = root
        self.info = info
        self.kwargs = kwargs

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
    def model_class(self):
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


class MutationResolver:
    @classmethod
    def as_function(cls, root, info, *args, **kwargs):
        model_class = get_model_class_from_info(info)
        resolver_class = getattr(model_class.Meta, 'mutation_resolver', cls)
        if not isinstance(resolver_class, Resolver):
            raise TypeError('Custom resolvers must inherit from Resolver')
        return resolver_class(root, info, *args, **kwargs).resolve()


class CreateResolver(MutationResolver):
    def resolve(self):
        model_class = self.model_class
        model = self.build_model(model_class)
        query = self.build_query(model)
        return resolve_get_query(self.root, self.info, query=query)

    def build_model(self, model_class):
        input = self.parse_input()
        return model_class(**input.change)

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
