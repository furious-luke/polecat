import os

from polecat.utils.container import Option, OptionDict, passthrough

from .context import active_context

__all__ = ('ConfigDict',)


class ConfigDict(OptionDict):
    def __init__(self, *args, prefix=None, **kwargs):
        self.prefix = ((prefix + '_') if prefix else '').upper()
        super().__init__(*args, **kwargs)

    def init_defaults(self, keys_to_add, defaults_to_add):
        prefix = self.__dict__['prefix']
        for key in keys_to_add:
            value = os.environ.get(f'{prefix}{key.upper()}')
            if value is not None:
                defaults_to_add[key] = value


active_context().Meta.add_options(
    Option('config', default=passthrough(ConfigDict)(
        (
            Option('debug', bool, False),
            Option('log_sql', bool, False),
            Option('jwt_secret'),
            Option('database_url')
        ),
        prefix='POLECAT'
    ))
)
