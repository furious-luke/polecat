from polecat.db.schema import Table
from polecat.model.db.helpers import model_to_table

from .models import Actor, Address


def test_construct_related():
    actor = Actor(
        first_name='Johnny',
        last_name='Depp',
        address={
            'country': 'USA'
        }
    )
    assert isinstance(actor.address, Address)
    assert actor.address.country == 'USA'


def test_construct_reverse():
    address = Address(
        country='USA',
        actors_by_address=[
            {
                'first_name': 'Johnny',
                'last_name': 'Depp'
            },
            {
                'first_name': 'Bill',
                'last_name': 'Murray'
            }
        ]
    )
    assert isinstance(address.actors_by_address, list)
    assert len(address.actors_by_address) == 2
    for actor in address.actors_by_address:
        assert isinstance(actor, Actor)
        assert actor.first_name is not None
        assert actor.last_name is not None
        assert actor.address == address


def test_model_to_table():
    actor_table = model_to_table(Actor)
    address_table = Table.registry['address']
    assert actor_table.C.id is not None
    assert actor_table.C.first_name is not None
    assert actor_table.C.last_name is not None
    assert actor_table.C.age is not None
    assert actor_table.C.address is not None
    assert actor_table.C.user is not None
    assert address_table.C.id is not None
    assert address_table.C.country is not None
    assert address_table.C.actors_by_address is not None
