import os

from polecat.db.connection import ConnectionManager


def test_uses_environment():
    # TODO: When pytest.org comes back online, find a nicer way.
    old_val = os.environ.get('DATABASE_URL')
    try:
        os.environ['DATABASE_URL'] = 'test'
        manager = ConnectionManager()
        assert manager.stack == ['test']
    finally:
        if old_val is not None:
            os.environ['DATABASE_URL'] = old_val
        else:
            del os.environ['DATABASE_URL']


def test_push_and_pop_url():
    manager = ConnectionManager()
    with manager.push_url(os.environ['DATABASE_URL']):
        with manager.connection():
            assert list(manager.connections.keys()) != []
        assert manager.stack == 2*[os.environ['DATABASE_URL']]
    assert manager.stack == [os.environ['DATABASE_URL']]
    assert list(manager.connections.keys()) == []


def test_connection_reuse():
    url = os.environ['DATABASE_URL']
    manager = ConnectionManager()
    assert url not in manager.connections
    with manager.connection() as conn:
        assert conn.status == 1
    assert url in manager.connections
    assert manager.connections[url].status == 1
    manager.close_all_connections()
    assert url not in manager.connections
