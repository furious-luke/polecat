from ..utils.registry import Registry, RegistryMetaclass

app_registry = Registry('app', construct=True)


class App(metaclass=RegistryMetaclass):
    _registry = app_registry
    _registry_base = 'App'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.models = []
        self.roles = []
        self.types = []
