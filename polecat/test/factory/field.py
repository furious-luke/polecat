from functools import partial

from factory import declarations
from factory.fuzzy import FuzzyDateTime, FuzzyInteger, FuzzyText
from polecat.utils import timezone

from ...core.registry import MappedRegistry, RegistryMetaclass
from ...model import field as mf

MappedRegistry('factory_field_registry')


class FactoryWrapper(declarations._FactoryWrapper):
    def __init__(self, factory_or_path):
        self.factory = None
        self.module = self.name = ''
        self.func = None
        if isinstance(factory_or_path, type):
            self.factory = factory_or_path
        elif callable(factory_or_path):
            self.func = factory_or_path
        else:
            if not (isinstance(factory_or_path, str) and '.' in factory_or_path):
                raise ValueError(
                    "A factory= argument must receive either a class "
                    "or the fully qualified path to a Factory subclass; got "
                    "%r instead." % factory_or_path)
            self.module, self.name = factory_or_path.rsplit('.', 1)

    def get(self):
        if self.factory is None:
            if self.func:
                self.factory = self.func()
        return super().get()


class SubFactory(declarations.SubFactory):
    def __init__(self, factory, **kwargs):
        super(declarations.SubFactory, self).__init__(**kwargs)
        self.factory_wrapper = FactoryWrapper(factory)


class Field(metaclass=RegistryMetaclass):
    _registry = 'factory_field_registry'
    _registry_base = 'Field'

    @classmethod
    def get_declaration(self, model_field, factory):
        raise NotImplemented


class TextField(Field):
    sources = (mf.TextField,)

    @classmethod
    def get_declaration(self, model_field, factory):
        return FuzzyText()


class NumberField(Field):
    sources = (mf.IntField,)

    @classmethod
    def get_declaration(self, model_field, factory):
        # TODO: 0 isn't good.
        return FuzzyInteger(0)


class DatetimeField(Field):
    sources = (mf.DatetimeField,)

    @classmethod
    def get_declaration(self, model_field, factory):
        return FuzzyDateTime(timezone.now())


class RelatedField(Field):
    sources = (mf.RelatedField,)

    @classmethod
    def get_declaration(self, model_field, factory):
        return SubFactory(partial(factory.get, model_field.other))
