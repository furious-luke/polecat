from polecat.core.registry import Registry, RegistryMetaclass
from polecat.utils import add_attribute, to_list
from polecat.utils.stringcase import camelcase, snakecase

from .field import Field, SerialField
from .omit import NONE


def model_registry_name_mapper(registry):
    return registry.Meta.name


Registry('type_registry', name_mapper=model_registry_name_mapper)
# TODO: Remaining registries.
model_registry = []
role_registry = []
query_registry = []
mutation_registry = []
access_registry = []


# TODO: Too much overlap between types and models.
class TypeMetaclass(RegistryMetaclass):
    def __new__(meta, name, bases, attrs):
        if not RegistryMetaclass.is_baseclass(name, bases):
            attrs['Meta'] = make_type_meta(
                name, bases, attrs,
                attrs.get('Meta')
            )
            cls = super().__new__(meta, name, bases, {
                k: v
                for k, v in attrs.items()
                if k not in attrs['Meta'].fields
            })
        else:
            cls = super().__new__(meta, name, bases, attrs)
        return cls

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        meta = getattr(cls, 'Meta', None)
        if meta:
            for field in meta.fields.values():
                field.prepare(cls)


class ModelMetaclass(type):
    def __new__(meta, name, bases, attrs):
        is_sub = bases and name != 'Model'
        if is_sub:
            attrs['Meta'] = make_model_meta(
                name, bases, attrs,
                attrs.get('Meta')
            )
            cls = super().__new__(meta, name, bases, {
                k: v
                for k, v in attrs.items()
                if k not in attrs['Meta'].fields
            })
        else:
            cls = super().__new__(meta, name, bases, attrs)
        if is_sub:
            model_registry.append(cls)
        return cls

    def __init__(cls, name, bases, attrs):
        meta = getattr(cls, 'Meta', None)
        if meta:
            # Must first dump all fields as any related field that
            # references "self" will cause an added reverse field to
            # be added.
            all_fields = tuple(meta.fields.values())
            for field in all_fields:
                field.prepare(cls)


class RoleMetaclass(type):
    def __new__(meta, name, bases, attrs):
        is_sub = bases and name != 'Role'
        if is_sub:
            attrs['Meta'] = make_role_meta(
                name, bases, attrs,
                attrs.get('Meta')
            )
        cls = super().__new__(meta, name, bases, make_role_attrs(attrs))
        if is_sub:
            role_registry.append(cls)
        return cls


class AccessMetaclass(type):
    def __new__(meta, name, bases, attrs):
        is_sub = bases and name != 'Access'
        # if is_sub:
        #     attrs['Meta'] = make_role_meta(
        #         name, bases, attrs,
        #         attrs.get('Meta')
        #     )
        cls = super().__new__(meta, name, bases, make_access_attrs(attrs))
        if is_sub:
            access_registry.append(cls)
        return cls


class QueryMetaclass(type):
    def __new__(meta, name, bases, attrs):
        is_sub = bases and name != 'Query'
        if is_sub:
            attrs['Meta'] = make_query_meta(
                name, bases, attrs,
                attrs.get('Meta')
            )
        cls = super().__new__(meta, name, bases, make_query_attrs(attrs))
        if is_sub:
            query_registry.append(cls)
        return cls


class MutationMetaclass(type):
    def __new__(meta, name, bases, attrs):
        is_sub = bases and name != 'Mutation'
        if is_sub:
            attrs['Meta'] = make_mutation_meta(
                name, bases, attrs,
                attrs.get('Meta')
            )
        cls = super().__new__(meta, name, bases, make_mutation_attrs(attrs))
        if is_sub:
            mutation_registry.append(cls)
        return cls


# TODO: So similar to models.
def make_type_meta(name, bases, attrs, meta):
    fields = {
        f.name: f
        for f in get_type_fields(attrs)
    }
    return type('Meta', (), {
        'options': meta.__dict__ if meta else {},
        'name': name,
        'fields': fields,
        'cc_fields': make_cc_fields(fields),
        'plural': get_plural(name, meta),
        'input': getattr(meta, 'input', False) if meta else False,  # TODO: Ugly
        'omit': getattr(meta, 'omit', NONE) if meta else NONE  # TODO: Ugly
    })


def make_model_meta(name, bases, attrs, meta):
    # TODO: Ugh.
    from .resolver import (
        CreateResolver, ResolverList, CreateResolverManager,
        UpdateResolverManager, UpdateResolver, UpdateOrCreateResolverManager,
        AllResolver, AllResolverManager, GetResolver, GetResolverManager,
        DeleteResolver, DeleteResolverManager
    )
    fields = {
        f.name: f
        for f in get_model_fields(attrs)
    }
    query_resolvers = to_list(getattr(meta, 'query_resolvers', []))
    mutation_resolvers = to_list(getattr(meta, 'mutation_resolvers', []))
    return type('Meta', (), {
        'options': meta.__dict__ if meta else {},
        'app': getattr(meta, 'app', None),
        'name': name,
        'table_name': name.lower(),
        'fields': fields,
        'cc_fields': make_cc_fields(fields),
        'plural': get_plural(name, meta),
        'uniques': getattr(meta, 'uniques', ()) if meta else (),
        'checks': getattr(meta, 'checks', ()) if meta else (),
        'omit': getattr(meta, 'omit', NONE) if meta else NONE,  # TODO: Duplicate of above
        'query_resolvers': ResolverList(query_resolvers),
        'all_resolvers': ResolverList(AllResolver()),
        'get_resolvers': ResolverList(GetResolver()),
        'all_resolver_manager': AllResolverManager(),
        'get_resolver_manager': GetResolverManager(),
        'mutation_resolvers': ResolverList(mutation_resolvers),
        'create_resolvers': ResolverList(CreateResolver()),
        'update_resolvers': ResolverList(UpdateResolver()),
        'delete_resolvers': ResolverList(DeleteResolver()),
        'create_resolver_manager': CreateResolverManager(),
        'update_resolver_manager': UpdateResolverManager(),
        'update_or_create_resolver_manager': UpdateOrCreateResolverManager(),
        'delete_resolver_manager': DeleteResolverManager()
    })


def make_role_meta(name, bases, attrs, meta):
    return type('Meta', (), {
        'options': meta.__dict__ if meta else {},
        'app': None,
        'name': name,
        'role': make_role_from_name(name)
    })


def make_query_meta(name, bases, attrs, meta):
    return type('Meta', (), {
        'options': meta,
        'name': name,
        'omit': getattr(meta, 'omit', NONE) if meta else NONE  # TODO: Duplicate of above
    })


def make_mutation_meta(name, bases, attrs, meta):
    return type('Meta', (), {
        'options': meta,
        'name': name,
        'omit': getattr(meta, 'omit', NONE) if meta else NONE  # TODO: Duplicate of above
    })


def make_role_attrs(attrs):
    return {
        'app': None,
        **attrs,
        'parents': attrs.get('parents', ())
    }


def make_access_attrs(attrs):
    return {
        'app': None,
        'all': (),
        'select': (),
        'insert': (),
        'update': (),
        'delete': (),
        **attrs
    }


def make_query_attrs(attrs):
    return {
        **attrs
    }


def make_mutation_attrs(attrs):
    return attrs


def get_type_fields(attrs):
    for name, field in attrs.items():
        if is_field_class(field):
            yield add_attribute(
                add_attribute(field, 'name', name),
                'cc_name', camelcase(name)
            )


def get_model_fields(attrs):
    yield add_attribute(
        add_attribute(
            SerialField(primary_key=True), 'name', 'id'
        ), 'cc_name', 'id'
    )
    for field in get_type_fields(attrs):
        yield field


def make_cc_fields(fields):
    return {
        f.cc_name: f
        for f in fields.values()
    }


def get_plural(name, meta):
    return getattr(meta, 'plural', f'{name}s')


def is_field_class(value):
    try:
        return issubclass(value.__class__, Field)
    except TypeError:
        return False


def make_role_from_name(name):
    name = snakecase(name)
    if name[-5:] == '_role':
        name = name[:-5]
    return name
