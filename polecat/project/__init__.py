import os
from importlib import import_module

from .project import Project  # noqa


def load_project():
    module_path = os.environ.get('POLECAT_PROJECT')
    if module_path is None:
        raise Exception('Please set POLECAT_PROJECT')
    parts = module_path.split('.')
    module_name, class_name = '.'.join(parts[:-1]), parts[-1]
    project_class = getattr(import_module(module_name), class_name)
    return project_class()
