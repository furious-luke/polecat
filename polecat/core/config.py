import os

from ..utils.container import OptionDict
from .context import active_context

__all__ = ('ConfigDict',)


class ConfigDict(OptionDict):
    def __init__(self, *args, prefix=None, **kwargs):
        self.__dict__['prefix'] = ((prefix + '_') if prefix else '').upper()
        super().__init__(*args, **kwargs)

    def _init_defaults(self, keys_to_add, defaults_to_add):
        prefix = self.__dict__['prefix']
        for key in keys_to_add:
            value = os.environ.get(f'{prefix}{key.upper()}')
            if value is not None:
                defaults_to_add[key] = value


active_context()._add_options(('config', ConfigDict(
    (
        ('debug', False),
        ('log_sql', False),
        'jwt_secret',
        'database_url'
    )
)))
