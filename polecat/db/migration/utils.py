import inspect
from pathlib import Path


def project_migrations_path():
    from ...project.project import get_active_project
    return Path(inspect.getfile(get_active_project().__class__)).parent / 'migrations'
