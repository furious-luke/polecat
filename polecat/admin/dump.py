import ujson as json

from ..db.query import Q

from .command import Command


class Dump(Command):
    def get_params(self):
        return (
            self.Option(('--ignore-model',), multiple=True),
        )

    def run(self, ignore_model=None):
        from ..project.project import get_active_project
        ignore_models = ignore_model or []
        project = get_active_project()
        schema = project.schema
        tables = {}
        for table in schema.tables:
            if table.name in ignore_models:
                continue
            all_rows = list(
                Q(table)
                .select()
            )
            tables[table.name] = all_rows
        print(json.dumps(tables, indent=2))
