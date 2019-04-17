import pytest
from polecat.deploy.event import HttpEvent
from polecat.project.project import Project


def test_index_html():
    project = Project()
    project.prepare()
    html = project.get_index_html()
    assert html is not None
    assert len(html) > 0


@pytest.mark.asyncio
async def test_index_handler():
    project = Project()
    project.prepare()
    event = {}
    request = type('Request', (), {
        'method': 'GET',
        'path': '/'
    })
    result = await project.handle_event(HttpEvent(event, request))
    assert len(result) == 2
    assert result[1] == 200
    assert len(result[0]) > 0
