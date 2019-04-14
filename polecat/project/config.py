default_config = {
    'log_sql': False
}


class Configuration:
    def __getattr__(self, key):
        return self.config[key]

    @property
    def project(self):
        # TODO: Cache.
        # TODO: Grrrrrr.
        from .project import get_active_project
        return get_active_project()

    @property
    def config(self):
        return self.project.config if self.project else default_config
