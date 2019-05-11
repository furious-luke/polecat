from polecat.core.context import active_context
from polecat.core.registry import Registry


def test_registry_and_context():
    a_registry = Registry('a_registry')
    b_registry = Registry('b_registry')
    ctx = active_context()
    assert ctx.registries.a_registry == a_registry
    assert ctx.registries.b_registry == b_registry
