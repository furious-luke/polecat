from polecat.utils import to_tuple
from polecat.utils.singledict import SingleDict

from .model import Mutation, Type


class Blueprint:
    def __init__(self):
        self.models = SingleDict()
        self.types = SingleDict()
        self.roles = SingleDict()
        self.access = []
        self.queries = SingleDict()
        self.mutations = SingleDict()
        self.hooks = []

    def add_model(self, model):
        self.models[model.Meta.name] = model
        self.add_model_hooks(model)

    def add_model_hooks(self, model):
        self.add_model_field_hooks(model)
        hooks = to_tuple(getattr(model.Meta, 'hooks', ()))
        context = HookContext(self, model_class=model)
        for hook in hooks:
            self.add_hook(hook, context)

    def add_model_field_hooks(self, model):
        for field_name, field in model.Meta.fields.items():
            hooks = to_tuple(getattr(field, 'hooks', ()))
            context = HookContext(
                self, model_class=model, field=field, field_name=field_name
            )
            for hook in hooks:
                self.add_hook(hook, context)

    def add_type(self, type):
        self.types[type.Meta.name] = type

    def add_role(self, role):
        # TODO: Should really be using name...
        self.roles[role.Meta.role] = role

    def add_access(self, access):
        self.access.append(access)

    def add_query(self, query):
        self.queries[query.Meta.name] = query

    def add_mutation(self, mutation):
        self.mutations[mutation.name] = mutation

    def create_type(self, name, fields):
        type(name, (Type,), {**fields})

    def create_mutation(self, name, resolver, return_type, input_type=None):
        cls = type(name, (Mutation,), {
            'returns': return_type,
            'input': input_type
        })
        cls.resolve = classmethod(resolver)

    def add_hook(self, callback, context=None):
        self.hooks.append((callback, context))

    def run_hooks(self):
        default_context = HookContext(self)
        for hook, context in self.hooks:
            if context is None:
                context = default_context
            hook(context)

    def get_mutation(self, name):
        return self.mutations[name]

    def iter_models(self):
        return self.models.values()

    def iter_types(self):
        return self.types.values()

    def iter_roles(self):
        return self.roles.values()

    def iter_access(self):
        return self.access

    def iter_queries(self):
        return self.queries.values()

    def iter_mutations(self):
        return self.mutations.values()


class HookContext:
    def __init__(self, blueprint, model_class=None, field=None,
                 field_name=None):
        self.blueprint = blueprint
        self.model_class = model_class
        self.field = field
        self.field_name = field_name
