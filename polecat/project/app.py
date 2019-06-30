import inspect
from pathlib import Path

from polecat.core.registry import Registry, RegistryMetaclass

Registry('app_registry', construct=True)


class App(metaclass=RegistryMetaclass):
    _registry = 'app_registry'
    _registry_base = 'App'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = self.__class__.__name__
        if self.name.endswith('App'):
            self.name = self.name[:-3]
        self.models = []
        self.roles = []
        self.types = []
        self.access = []

    def __eq__(self, other):
        if not isinstance(other, App):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @property
    def path(self):
        return Path(inspect.getfile(self.__class__)).parent
