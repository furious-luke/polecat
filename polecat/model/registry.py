from polecat.utils import add_attribute, to_list
from polecat.utils.stringcase import camelcase, snakecase

from .defaults import default_blueprint
from .field import Field, SerialField
from .omit import NONE


class RegisteredType(type):
    BASE_TYPE_NAME = None

    def build_type(metaclass, name, bases, attrs):
        cls = super().__new__(metaclass, name, bases, attrs)
        if metaclass.is_sub_type(metaclass, name, bases):
            metaclass.register_type(metaclass, cls)
        return cls

    def is_sub_type(metaclass, name, bases):
        return bases and name != metaclass.BASE_TYPE_NAME

    def register_type(metaclass, cls):
        pass


class ConstructableMetaType(RegisteredType):
    def build_type(metaclass, name, bases, attrs):
        is_sub = metaclass.is_sub_type(metaclass, name, bases)
        if is_sub:
            meta = metaclass.build_meta(
                metaclass, name, attrs, attrs.get('Meta')
            )
            if meta is not None:
                attrs['Meta'] = meta
            cls = super().__new__(metaclass, name, bases, {
                k: v
                for k, v in attrs.items()
                if k not in attrs['Meta'].fields
            })
        else:
            cls = super().__new__(metaclass, name, bases, attrs)
        if is_sub:
            metaclass.register_type(metaclass, cls)
        return cls

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        meta = getattr(cls, 'Meta', None)
        if meta:
            # Must first dump all fields as any related field that
            # references "self" will cause an added reverse field to
            # be added.
            all_fields = tuple(meta.fields.values())
            for field in all_fields:
                field.prepare(cls)

    def build_meta(metaclass, name, attrs, meta):
        return None


class TypeMetaclass(ConstructableMetaType):
    BASE_TYPE_NAME = 'Type'

    def __new__(meta, name, bases, attrs):
        return meta.build_type(meta, name, bases, attrs)

    def build_meta(metaclass, name, attrs, meta):
        return make_type_meta(name, attrs, meta)

    def register_type(metaclass, cls):
        default_blueprint.add_type(cls)


class ModelMetaclass(ConstructableMetaType):
    BASE_TYPE_NAME = 'Model'

    def __new__(metaclass, name, bases, attrs):
        return metaclass.build_type(metaclass, name, bases, attrs)

    def build_meta(metaclass, name, attrs, meta):
        return make_model_meta(name, attrs, meta)

    def register_type(metaclass, cls):
        default_blueprint.add_model(cls)


class RoleMetaclass(RegisteredType):
    BASE_TYPE_NAME = 'Role'

    def __new__(metaclass, name, bases, attrs):
        is_sub = metaclass.is_sub_type(metaclass, name, bases)
        if is_sub:
            attrs['Meta'] = make_role_meta(
                name, bases, attrs, attrs.get('Meta')
            )
        cls = super().__new__(metaclass, name, bases, make_role_attrs(attrs))
        if is_sub:
            metaclass.register_type(metaclass, cls)
        return cls

    def register_type(metaclass, cls):
        default_blueprint.add_role(cls)


class AccessMetaclass(RegisteredType):
    BASE_TYPE_NAME = 'Access'

    def __new__(metaclass, name, bases, attrs):
        is_sub = metaclass.is_sub_type(metaclass, name, bases)
        cls = super().__new__(metaclass, name, bases, make_access_attrs(attrs))
        if is_sub:
            metaclass.register_type(metaclass, cls)
        return cls

    def register_type(metaclass, cls):
        default_blueprint.add_access(cls)


class QueryMetaclass(RegisteredType):
    BASE_TYPE_NAME = 'Query'

    def __new__(metaclass, name, bases, attrs):
        is_sub = metaclass.is_sub_type(metaclass, name, bases)
        if is_sub:
            attrs['Meta'] = make_query_meta(
                name, bases, attrs, attrs.get('Meta')
            )
        cls = super().__new__(metaclass, name, bases, make_query_attrs(attrs))
        if is_sub:
            metaclass.register_type(metaclass, cls)
        return cls

    def register_type(metaclass, cls):
        default_blueprint.add_query(cls)


class MutationMetaclass(RegisteredType):
    def __new__(metaclass, name, bases, attrs):
        is_sub = metaclass.is_sub_type(metaclass, name, bases)
        cls = super().__new__(
            metaclass, name, bases, make_mutation_attrs(name, attrs)
        )
        if is_sub:
            metaclass.register_type(metaclass, cls)
        return cls

    def register_type(metaclass, cls):
        default_blueprint.add_mutation(cls)


# TODO: So similar to models.
def make_type_meta(name, attrs, meta):
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


def make_model_meta(name, attrs, meta):
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
        'indexes': getattr(meta, 'indexes', ()),
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
    meta_name = getattr(meta, 'name', None)
    if meta_name is not None:
        name = meta_name
    elif name[-5:] == 'Query':
        name = name[:-5]
    # TODO: Ugh.
    from .resolver import QueryResolverManager
    resolver_manager = attrs.get('resolver_manager')
    if not resolver_manager:
        resolver_manager = QueryResolverManager()
    return type('Meta', (), {
        'options': meta,
        'name': name,
        'resolvers': attrs.get('resolvers', ()),
        'resolver_manager': resolver_manager,
        'omit': getattr(meta, 'omit', NONE) if meta else NONE  # TODO: Duplicate of above
    })


def make_mutation_attrs(name, attrs):
    # TODO: Ugh.
    from .resolver import MutationResolverManager
    resolver_manager = attrs.get('resolver_manager')
    if not resolver_manager:
        resolver_manager = MutationResolverManager()
    return {
        **attrs,
        'name': attrs.get('name', name),
        'resolvers': attrs.get('resolvers', ()),
        'resolver_manager': resolver_manager,
        'omit': getattr(attrs, 'omit', NONE)
    }


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
