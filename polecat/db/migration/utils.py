import inspect
from pathlib import Path

from ...utils import to_class


def project_migrations_path():
    from ...project.project import get_active_project
    active_project = get_active_project()
    if active_project is None:
        return Path.cwd()
    return Path(inspect.getfile(to_class(active_project))).parent / 'migrations'
