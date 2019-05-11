import pytest
from polecat.utils.container import OptionDict, passthrough

OptionDict = passthrough(OptionDict)


def setup_optiondict():
    od = OptionDict()
    od.Meta.add_options(
        'no_default',
        ('has_default', 'has_default_value'),
        'very_different'
    )
    return od


def test_dict_access():
    od = setup_optiondict()
    od['no_default'] = 'no_default_value'
    assert od['no_default'] == 'no_default_value'


def test_attribute_access():
    od = setup_optiondict()
    od.no_default = 'no_default_value'
    assert od.no_default == 'no_default_value'


def test_default_values():
    od = setup_optiondict()
    assert od.has_default == 'has_default_value'


def test_missing_option():
    od = setup_optiondict()
    with pytest.raises(ValueError):
        od.no_default
    with pytest.raises(KeyError):
        od.not_default
