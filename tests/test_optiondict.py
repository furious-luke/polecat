import pytest
from polecat.utils.optiondict import (BoolOption, ListOption, Option,
                                      OptionDict, UndefinedOptionError)
from polecat.utils.passthrough import passthrough

OptionDict = passthrough(OptionDict)


def setup_optiondict():
    od = OptionDict()
    od.Meta.add_options(
        Option('no_default'),
        Option('has_default', default='has_default_value'),
        Option('very_different'),
        BoolOption('a_bool', default=False),
        ListOption('a_list')
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
    with pytest.raises(UndefinedOptionError):
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


def test_list_option_assignment():
    od = setup_optiondict()
    od.a_list = []
    assert od.a_list == []
    od.a_list = [0]
    assert od.a_list == [0]
    od.a_list = 1
    assert od.a_list == [1]


def test_list_option_merge_value():
    od = setup_optiondict()
    od.a_list = [0]
    od.Meta.merge({
        'a_list': 1
    })
    assert od.a_list == [0, 1]


def test_list_option_merge_list():
    od = setup_optiondict()
    od.a_list = [0]
    od.Meta.merge({
        'a_list': [1, 2]
    })
    assert od.a_list == [0, 1, 2]
