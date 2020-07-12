from unittest.mock import MagicMock

import pytest
from polecat.db.sql.expression.alias import Alias


class SqlTermTester:
    @classmethod
    def test_get_alias(cls, term):
        term.term.get_alias.assert_not_called()
        term.get_alias()
        term.term.get_alias.assert_called_once()

    @classmethod
    def test_get_subrelation(cls, term):
        name = 'test'
        term.term.get_subrelation.assert_not_called()
        term.get_subrelation(name)
        term.term.get_subrelation.assert_called_once_with(name)

    @classmethod
    def test_get_column(cls, term):
        name = 'test'
        term.term.get_column.assert_not_called()
        term.get_column(name)
        term.term.get_column.assert_called_once_with(name)

    @classmethod
    def test_has_column(cls, term):
        name = 'test'
        term.term.has_column.assert_not_called()
        term.has_column(name)
        term.term.has_column.assert_called_once_with(name)

    @classmethod
    def test_push_selection(cls, term):
        selection = 'test'
        term.term.push_selection.assert_not_called()
        term.push_selection(selection)
        term.term.push_selection.assert_called_once_with(selection)


SqlTermTester.ALL_TESTS = set((
    SqlTermTester.test_get_alias,
    SqlTermTester.test_get_subrelation,
    SqlTermTester.test_get_column,
    SqlTermTester.test_has_column,
    SqlTermTester.test_push_selection
))


@pytest.fixture
def alias():
    return Alias(MagicMock())
