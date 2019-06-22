import os
from pathlib import Path

import click
import ujson


def load_config():
    cfg = read_config(global_config_path())
    path = find_config()
    cfg.update(read_config(path))
    return cfg, path


def update_config(new_cfg={}, delete=[], path=None):
    if path is None:
        path = find_config()
        if not path:
            path = os.path.join(os.getcwd(), 'polecat.json')
    cfg = read_config(path)
    for d in delete:
        try:
            del cfg[d]
        except KeyError:
            pass
    cfg.update(new_cfg)
    write_config(path, cfg)


def find_config():
    dir = Path().absolute()
    while True:
        path = dir / 'polecat.json'
        if path.exists():
            return str(path)
        if dir == Path.home():
            return None
        dir = dir.parent


def global_config_path():
    return os.path.join(click.get_app_dir('polecat'), 'polecat.json')


def read_config(path):
    cfg = {}
    if path and os.path.exists(path):
        data = open(path, 'r').read()
        if data:
            cfg = ujson.loads(data)
    return cfg


def write_config(path, cfg):
    if not os.path.exists(path):
        try:
            os.makedirs(os.path.dirname(path))
        except Exception:
            pass
        try:
            open(path, 'x')
        except Exception:
            pass
    os.chmod(path, 0o600)
    cfg_str = ujson.dumps(cfg, indent=2)
    open(path, 'w').write(cfg_str)
