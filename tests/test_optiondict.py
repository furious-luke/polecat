import pytest
from polecat.utils.container import Option, OptionDict, passthrough

OptionDict = passthrough(OptionDict)


def setup_optiondict():
    od = OptionDict()
    od.Meta.add_options(
        Option('no_default'),
        Option('has_default', default='has_default_value'),
        Option('very_different'),
        Option('a_bool', type=bool, default=False)
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


def test_boolean_option():
    od = setup_optiondict()
    assert od.a_bool == False  # noqa
    od.a_bool = 1
    assert od.a_bool == True  # noqa
    od.a_bool = 0
    assert od.a_bool == False  # noqa
    od.a_bool = 'yes'
    assert od.a_bool == True  # noqa
    od.a_bool = 'no'
    assert od.a_bool == False  # noqa
    od.a_bool = 'YES'
    assert od.a_bool == True  # noqa
    od.a_bool = 'NO'
    assert od.a_bool == False  # noqa
    od.a_bool = 'true'
    assert od.a_bool == True  # noqa
    od.a_bool = 'false'
    assert od.a_bool == False  # noqa
    od.a_bool = 'y'
    assert od.a_bool == True  # noqa
    od.a_bool = ''
    assert od.a_bool == False  # noqa
