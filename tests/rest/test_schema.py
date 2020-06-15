import pytest

from polecat.rest.schema import RestSchema, RestView
from polecat.rest.execute import run_http_query


@pytest.mark.asyncio
async def test_schema(mocker):
    a_mock = mocker.MagicMock()
    b_mock = mocker.MagicMock()
    schema = RestSchema(
        routes={
            '/a': RestView(a_mock),
            '/b': RestView(b_mock)
        }
    )
    request = type('Request', (), {
        'path': '/a'
    })
    result = await run_http_query(schema, request)
    assert result is not None
    a_mock.resolver_manager.assert_called()
    b_mock.resolver_manager.assert_not_called()
