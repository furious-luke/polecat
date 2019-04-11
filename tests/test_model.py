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
