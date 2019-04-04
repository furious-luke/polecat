from .project import get_active_project


class Configuration:
    def __getattr__(self, key):
        self.project.config[key]

    @property
    def project(self):
        # TODO: Cache.
        return get_active_project()
