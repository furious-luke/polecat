from polecat.db.migration.migration import Migration as BaseMigration
from polecat.db.migration.operation import CreateTable, RunPython
from polecat.db.migration.schema import Table, Column, RelatedColumn
from polecat.db.sql import Q
from starwars.models import Film, Planet, Character


def create_data(cursor):
    ep4 = Film(title='A New Hope')
    Q(ep4).insert().execute(cursor=cursor)
    tatooine = Planet(name='Tatooine', film=ep4)
    Q(tatooine).insert().execute(cursor=cursor)
    luke = Character(name='Luke Skywalker', film=ep4)
    Q(luke).insert().execute(cursor=cursor)


class Migration(BaseMigration):
    dependencies = []
    operations = [
        CreateTable(
            'film',
            columns=[
                Column('id', 'serial', primary_key=True),
                Column('title', 'text', null=False)
            ]
        ),
        CreateTable(
            'planet',
            columns=[
                Column('id', 'serial', primary_key=True),
                Column('name', 'text', null=False),
                RelatedColumn('film', 'int', 'film.id')
            ]
        ),
        CreateTable(
            'character',
            columns=[
                Column('id', 'serial', primary_key=True),
                Column('name', 'text', null=False),
                RelatedColumn('film', 'int', 'film.id')
            ]
        ),
        RunPython(create_data)
    ]
