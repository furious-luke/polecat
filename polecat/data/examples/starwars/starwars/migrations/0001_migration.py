from polecat.db.migration import migration, operation
from polecat.db.query import Q
from polecat.db.schema import column


def create_data(schema, cursor):
    film_table = schema.get_table_by_name('film')
    planet_table = schema.get_table_by_name('planet')
    char_table = schema.get_table_by_name('character')
    insert_ep4 = Q(film_table).insert(title='A New Hope')
    Q.common(
        Q(planet_table).insert(
            name='Tatooine',
            film=insert_ep4
        ),
        Q(char_table).insert(
            name='Luke Skywalker',
            film=insert_ep4
        )
    ).execute(cursor=cursor)


class Migration(migration.Migration):
    dependencies = []
    operations = [
        operation.CreateTable(
            'film',
            columns=[
                column.SerialColumn('id', unique=False, null=True, primary_key=True),
                column.TextColumn('title', unique=False, null=False, primary_key=False)
            ]
        ),
        operation.CreateTable(
            'planet',
            columns=[
                column.SerialColumn('id', unique=False, null=True, primary_key=True),
                column.TextColumn('name', unique=False, null=False, primary_key=False),
                column.RelatedColumn('film', unique=False, null=True, primary_key=False, related_table='film', related_column='planets_by_film')
            ]
        ),
        operation.CreateTable(
            'character',
            columns=[
                column.SerialColumn('id', unique=False, null=True, primary_key=True),
                column.TextColumn('name', unique=False, null=False, primary_key=False),
                column.RelatedColumn('film', unique=False, null=True, primary_key=False, related_table='film', related_column='characters_by_film')
            ]
        ),
        operation.RunPython(create_data)
    ]
