from polecat.db.migration import Migration as BaseMigration
from polecat.db.migration import operation
from polecat.db.query import Q
from polecat.db.schema import Column, RelatedColumn


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
    ).execute()


class Migration(BaseMigration):
    dependencies = []
    operations = [
        operation.CreateTable(
            'film',
            columns=[
                Column('id', 'serial', primary_key=True),
                Column('title', 'text', null=False)
            ]
        ),
        operation.CreateTable(
            'planet',
            columns=[
                Column('id', 'serial', primary_key=True),
                Column('name', 'text', null=False),
                RelatedColumn('film', 'int', 'film.id')
            ]
        ),
        operation.CreateTable(
            'character',
            columns=[
                Column('id', 'serial', primary_key=True),
                Column('name', 'text', null=False),
                RelatedColumn('film', 'int', 'film.id')
            ]
        ),
        operation.RunPython(create_data)
    ]
