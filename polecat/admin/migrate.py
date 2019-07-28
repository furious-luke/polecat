from .command import Command


class Migrate(Command):
    def get_params(self):
        return (
            self.Option(('--skip',), is_flag=True, default=False),
        )

    def run(self, skip):
        from polecat.db.migration import migrate
        migrate(
            apps=self.project.apps,
            migration_paths=(self.project.path,)
        )
