import ujson as json

from ..db.decorators import dbcursor
from ..db.query import Q

from .command import Command


class Restore(Command):
    def get_params(self):
        return (
            self.Argument(('dump-file',)),
        )

    @dbcursor
    def run(self, dump_file, cursor=None):
        from ..project.project import get_active_project
        project = get_active_project()
        schema = project.schema
        with open(dump_file, 'r') as f:
            tables = json.loads(f.read())
        for table in schema.tables:
            all_rows = tables.get(table.name)
            if all_rows:
                for row in all_rows:
                    (
                        Q(table)
                        .insert(**row)
                        .execute()
                    )
                    cursor.execute(
                        f"SELECT setval('{table.name}_id_seq',"
                        f"(SELECT MAX(id) FROM {table.name}))"
                    )
                print(f'Restored {len(all_rows)} row(s) for table {table.name}')
