from polecat.test.utils import environ
from polecat.utils.config import Config


def define_config():
    class TestConfig(Config):
        value = str
    return TestConfig()


def test_config():
    config = define_config()
    with environ(POLECAT_VALUE='hello'):
        assert config.value == 'hello'
