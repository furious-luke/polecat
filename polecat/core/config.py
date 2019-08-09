from polecat.utils.config import Config
from polecat.utils.optiondict import Option
from polecat.utils.proxy import Proxy


class RootConfig(Config):
    debug = (bool, False)
    log_sql = (bool, False)
    jwt_secret = str
    database_url = str


def mount_config(config, path):
    segments = path.split('.')
    cur_config = default_config
    for segment in segments[:-1]:
        cur_config = getattr(cur_config, segment)
    if cur_config.Meta.has_option(segments[-1]):
        cur_config = getattr(cur_config, segments[-1])
        for name, option in config.Meta.options.items():
            cur_config.Meta.add_option(option)
    else:
        prefix = ''.join([cur_config.Meta.prefix, segments[-1].upper()])
        config.Meta.set_prefix(prefix)
        cur_config.Meta.add_option(Option(segments[-1], config))


def auto_mount_config(path):
    def inner(cls):
        mount_config(cls(), path)
        return cls
    return inner


default_config = Proxy(lambda: RootConfig(prefix='POLECAT'))
