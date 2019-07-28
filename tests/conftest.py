import pytest
from polecat.deploy.aws.server import LambdaServer
from polecat.deploy.server.server import Server
from polecat.project.project import Project, set_active_project

from .models import DefaultRole


def build_test_project():
    class TestProject(Project):
        default_role = DefaultRole
    return TestProject()


@pytest.fixture
def active_project():
    global global_active_project
    project = build_test_project()
    set_active_project(project)
    try:
        yield project
    finally:
        set_active_project(None)


@pytest.fixture
def sanic_server():
    project = build_test_project()
    yield Server(project=project)


@pytest.fixture
def lambda_server():
    project = build_test_project()
    yield LambdaServer(project=project)
