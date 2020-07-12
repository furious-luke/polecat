import pytest
from polecat.project.app import App
from polecat.db.schema import Table, RelatedColumn

APP_NAME = 'table'
TABLE_NAME = 'test'
APP_TABLE_NAME = f'{APP_NAME}_{TABLE_NAME}'
SUBRELATION_TABLE_NAME = 'subrt'
SUBRELATION_COLUMN_NAME = 'subrc'


class TableApp(App):
    pass


@pytest.fixture
def table():
    _table = Table(
        TABLE_NAME,
        columns=[
            RelatedColumn(SUBRELATION_COLUMN_NAME, Table(SUBRELATION_TABLE_NAME))
        ],
        app=TableApp()
    )
    _table.bind_all_columns()
    return _table
