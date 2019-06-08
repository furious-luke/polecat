from psycopg2.sql import SQL, Identifier


class Delete:
    @classmethod
    def evaluate(self, model):
        return (
            SQL('DELETE FROM {} WHERE id=%s').format(
                Identifier(model.Meta.table_name)
            ),
            (model.id,)
        )
