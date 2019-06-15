from polecat.db.schema import Role, Table
from polecat.model.db.helpers import model_to_table

from .models import Actor, Address, schema


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


def test_create_schema():
    address_table = schema.get_table_by_name('address')
    actor_table = schema.get_table_by_name('actor')
    admin_role = schema.get_role_by_name('admin')
    address_access = schema.get_access_by_entity(address_table)
    assert actor_table.C.id is not None
    assert actor_table.C.first_name is not None
    assert actor_table.C.last_name is not None
    assert actor_table.C.age is not None
    assert actor_table.C.address is not None
    assert actor_table.C.user is not None
    assert address_table.C.id is not None
    assert address_table.C.country is not None
    assert address_table.C.actors_by_address is not None
    assert admin_role.name == 'admin'
    assert address_access.entity == address_table


def test_role_to_dbrole_converts_parents():
    user_role = schema.get_role_by_name('user')
    parent = list(user_role.parents)[0]
    assert parent.__class__ == Role
