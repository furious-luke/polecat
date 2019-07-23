from polecat.utils import substitute
from polecat.utils.feedback import feedback
from termcolor import colored

from .constants import PROJECT_PREFIX, PROJECT_REGISTRY
from .exceptions import EntityDoesNotExist, EntityExists, KnownError
from .operations import (attach_group_policy, create_group, create_policy,
                         delete_group, delete_parameter, delete_policy,
                         detach_group_policy, find_policy, get_parameter,
                         set_parameter)
from .policy import project_policy
from .utils import aws_client


@feedback
def create_project(project, bucket, feedback):
    iam = aws_client('iam')
    ssm = aws_client('ssm')
    with feedback(f'Create project {colored(project, "blue")}'):
        add_project_to_registry(project, ssm=ssm)
    with feedback(f'Create project group'):
        create_project_group(project, iam=iam)
    with feedback(f'Create project policy'):
        create_project_group_policy(project, bucket, iam=iam)
    with feedback(f'Attach project group'):
        attach_project_group(project, iam=iam)


@feedback
def list_projects(feedback):
    ssm = aws_client('ssm')
    with feedback(f'List projects'):
        projects = get_parameter(PROJECT_REGISTRY, default=[], ssm=ssm)
        return [p for p in projects if p != '_']


@feedback
def delete_project(project, feedback):
    iam = aws_client('iam')
    ssm = aws_client('ssm')
    assert_project_exists(project, ssm=ssm)
    with feedback(f'Delete project {colored(project, "blue")}'):
        assert_project_is_empty(project, ssm=ssm)
        # TODO: Need to fetch the path, then delete all of them.
        delete_parameter(PROJECT_PREFIX.format(project), ssm=ssm)
        delete_project_from_registry(project, ssm=ssm)
    with feedback(f'Detach project policy'):
        detach_project_group(project, iam=iam)
    with feedback(f'Delete project policy'):
        delete_project_group_policy(project, iam=iam)
    with feedback(f'Delete project group'):
        delete_project_group(project, iam=iam)


def add_project_to_registry(project, ssm=None):
    registry = get_parameter(PROJECT_REGISTRY, ssm=ssm)
    if project in registry:
        raise EntityExists
    try:
        registry.remove('_')
    except ValueError:
        pass
    registry.append(project)
    set_parameter(PROJECT_REGISTRY, registry)


def delete_project_from_registry(project, ssm=None):
    registry = get_parameter(PROJECT_REGISTRY, ssm=ssm)
    registry.remove(project)
    if not registry:
        registry.append('_')
    set_parameter(PROJECT_REGISTRY, registry)


def create_project_group(project, iam=None):
    create_group(project, iam=iam)


def delete_project_group(project, iam=None):
    delete_group(project, iam=iam)


def create_project_group_policy(project, bucket, iam=None):
    create_policy(
        project,
        substitute(project_policy, project=project, bucket=bucket),
        iam=iam
    )


def delete_project_group_policy(project, iam=None):
    delete_policy(project, iam=iam)


def attach_project_group(project, iam=None):
    attach_group_policy(project, find_policy(project).arn, iam=iam)


def detach_project_group(project, iam=None):
    detach_group_policy(project, find_policy(project).arn, iam=iam)


def project_exists(project, ssm=None):
    registry = get_parameter(PROJECT_REGISTRY, ssm=ssm)
    return project in registry


def assert_project_exists(project, ssm=None):
    if not project_exists(project, ssm=ssm):
        raise EntityDoesNotExist(
            f'Project {colored(project, "blue")} does not exist'
        )


def assert_project_is_empty(project, ssm=None):
    param = PROJECT_PREFIX.format(project) + 'deploymentRegistry'
    deployments = get_parameter(param, ssm=ssm)
    if len(deployments) > 1 or (len(deployments) == 1 and deployments[0] != '_'):
        raise KnownError('project is not empty')
