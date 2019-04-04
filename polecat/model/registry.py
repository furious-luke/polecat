from ..utils import add_attribute
from ..utils.stringcase import camelcase, snakecase
from .field import Field, IntField

type_registry = []
model_registry = []
role_registry = []
query_registry = []
mutation_registry = []


class TypeMetaclass(type):
    def __new__(meta, name, bases, attrs):
        is_sub = bases and name != 'Type'
        if is_sub:
            attrs['Meta'] = make_type_meta(
                name, bases, attrs,
                attrs.get('Meta')
            )
        cls = super().__new__(meta, name, bases, attrs)
        if is_sub:
            type_registry.append(cls)
        return cls


class ModelMetaclass(type):
    def __new__(meta, name, bases, attrs):
        is_sub = bases and name != 'Model'
        if is_sub:
            attrs['Meta'] = make_model_meta(
                name, bases, attrs,
                attrs.get('Meta')
            )
        cls = super().__new__(meta, name, bases, attrs)
        if is_sub:
            model_registry.append(cls)
        return cls


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
        'options': meta,
        'name': name,
        'fields': fields,
        'cc_fields': make_cc_fields(fields),
        'plural': get_plural(name),
        'input': getattr(meta, 'input', False) if meta else False  # TODO: Ugly
    })


def make_model_meta(name, bases, attrs, meta):
    fields = {
        f.name: f
        for f in get_fields(attrs)
    }
    return type('Meta', (), {
        'options': meta,
        'name': name,
        'table': snakecase(name),  # TODO
        'fields': fields,
        'cc_fields': make_cc_fields(fields),
        'plural': get_plural(name)
    })


def make_role_meta(name, bases, attrs, meta):
    return type('Meta', (), {
        'options': meta,
        'name': name,
        'role': make_role_from_name(name)
    })


def make_query_meta(name, bases, attrs, meta):
    return type('Meta', (), {
        'options': meta,
        'name': name
    })


def make_mutation_meta(name, bases, attrs, meta):
    return type('Meta', (), {
        'options': meta,
        'name': name
    })


def make_role_attrs(attrs):
    return {
        **attrs,
        'parents': attrs.get('parents', ())
    }


def make_query_attrs(attrs):
    return {
        **attrs
    }


def make_mutation_attrs(attrs):
    return attrs


def get_type_fields(attrs):
    for k, v in attrs.items():
        if is_field_class(v):
            yield add_attribute(
                add_attribute(v, 'name', k),
                'cc_name', camelcase(k)
            )


def get_fields(attrs):
    yield add_attribute(
        add_attribute(
            IntField(primary_key=True), 'name', 'id'
        ), 'cc_name', 'id'
    )
    for field in get_type_fields(attrs):
        yield field


def make_cc_fields(fields):
    return {
        f.cc_name: f
        for f in fields.values()
    }


def get_plural(name):
    return f'{name}s'


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
