import pytest

from .conftest import APP_NAME, TABLE_NAME, APP_TABLE_NAME, SUBRELATION_COLUMN_NAME, SUBRELATION_TABLE_NAME


def test_get_name(table):
    table.app = None
    assert table.name == TABLE_NAME


def test_get_name_with_app(table):
    assert table.name == APP_TABLE_NAME


def test_get_alias(table):
    assert table.get_alias() == APP_TABLE_NAME


def test_root_relation(table):
    assert table.get_root_relation() == table


def test_get_subrelation(table):
    assert table.get_subrelation(SUBRELATION_COLUMN_NAME).name == SUBRELATION_TABLE_NAME


def test_get_subrelation_with_missing_name(table):
    with pytest.raises(KeyError):
        table.get_subrelation('missing')


def test_push_selection(table):
    table.push_selection()
