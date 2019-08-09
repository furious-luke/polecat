import pytest
from polecat.core.config import RootConfig, default_config
from polecat.deploy.aws.server import LambdaServer
from polecat.deploy.server.server import Server
from polecat.model import Blueprint, default_blueprint
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


@pytest.fixture
def push_blueprint():
    old_bp = default_blueprint.get_target()
    try:
        bp = Blueprint()
        default_blueprint.set_target(bp)
        yield bp
    finally:
        default_blueprint.set_target(old_bp)


@pytest.fixture
def push_config():
    old_cfg = default_config.get_target()
    try:
        cfg = RootConfig(prefix='POLECAT')
        default_config.set_target(cfg)
        yield cfg
    finally:
        default_config.set_target(old_cfg)
