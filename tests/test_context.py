from polecat.core.context import active_context
from polecat.utils.container import OptionDict


def test_active_context():
    @active_context
    def wrapped(context=None):
        return context
    assert isinstance(active_context(), OptionDict)
    assert isinstance(wrapped(), OptionDict)
