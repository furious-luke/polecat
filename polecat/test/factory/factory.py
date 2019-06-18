from factory import base
from polecat.model.db import Q

from ...core.context import active_context
from ...model.field import ReverseField
from ...model.registry import model_registry
from .field import *  # noqa


class ModelFactory(base.Factory):
    # _options_class = FactoryOptions

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        inst = model_class(*args, **kwargs)
        Q(inst).insert().into(inst)
        return inst


class FactoryContainer:
    @classmethod
    def get(cls, model):
        return getattr(cls, model.__name__)


def create_model_factory():
    factory = type('Factory', (FactoryContainer,), {})
    for model in model_registry:
        setattr(
            factory,
            model.__name__,
            create_factory_for_model(model, factory)
        )
    return factory


def create_factory_for_model(model, factory):
    name = f'Auto{model.Meta.name}'
    return type(name, (ModelFactory,), {
        **{
            f.name: create_factory_field(f, factory)
            for f in iter_model_fields(model)
        },
        'Meta': type('Meta', (), {
            'model': model
        })
    })


def iter_model_fields(model):
    for field in model.Meta.fields.values():
        # TODO: Should test for auto instead.
        if getattr(field, 'primary_key', False):
            continue
        # Don't instantiate reverses by default, gets us into infinite
        # loops.
        if isinstance(field, ReverseField):
            continue
        yield field


@active_context
def create_factory_field(field, factory, context=None):
    return (
        context.registries.factory_field_registry[field]
        .get_declaration(field, factory)
    )
