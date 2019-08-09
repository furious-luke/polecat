from polecat.core.config import default_config, mount_config
from polecat.test.utils import environ
from polecat.utils.config import Config


def define_config():
    class TestConfig(Config):
        value = str
    return TestConfig()


def define_nested():
    class NestedConfig(Config):
        other = str
    return NestedConfig()


def test_config_default():
    config = define_config()
    with environ(VALUE='hello'):
        assert config.value == 'hello'


def test_mount_config(push_config):
    config = define_config()
    mount_config(config, 'base')
    with environ(POLECAT_BASE_VALUE='hello'):
        assert default_config.base.value == 'hello'


def test_nested_mount(push_config):
    config = define_config()
    mount_config(config, 'base')
    nested = define_nested()
    mount_config(nested, 'base.nested')
    with environ(POLECAT_BASE_NESTED_OTHER='hello'):
        assert default_config.base.nested.other == 'hello'


def test_merged_mount(push_config):
    config = define_config()
    mount_config(config, 'base')
    nested = define_nested()
    mount_config(nested, 'base')
    with environ(POLECAT_BASE_VALUE='hello'):
        assert default_config.base.value == 'hello'
    with environ(POLECAT_BASE_OTHER='hello'):
        assert default_config.base.other == 'hello'
