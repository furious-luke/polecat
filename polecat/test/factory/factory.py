from factory import base

from ...db.sql import Q
from ...model.registry import model_registry
from .field import factory_field_registry

# class FactoryOptions(base.FactoryOptions):
#     def contribute_to_class(self, factory, meta=None, base_meta=None,
#                             base_factory=None, params=None):
#         super().contribute_to_class(factory, meta=meta, base_meta=base_meta,
#                                     base_factory=base_factory, params=params)
#         import pdb; pdb.set_trace()
#         print('h')


class ModelFactory(base.Factory):
    # _options_class = FactoryOptions

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        inst = model_class(*args, **kwargs)
        Q(inst).insert().execute()
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
        if getattr(field, 'reverse', False):
            continue
        yield field


def create_factory_field(field, factory):
    return factory_field_registry[field].get_declaration(field, factory)
