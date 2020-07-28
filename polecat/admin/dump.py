import ujson as json

from ..db.query import Q

from .command import Command


class Dump(Command):
    def run(self):
        from ..project.project import get_active_project
        project = get_active_project()
        schema = project.schema
        tables = {}
        for table in schema.tables:
            all_rows = list(
                Q(table)
                .select()
            )
            tables[table.name] = all_rows
        print(json.dumps(tables, indent=2))
