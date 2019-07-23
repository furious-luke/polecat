from termcolor import colored

from ...utils.feedback import feedback
from .constants import DEPLOYMENT_PREFIX, DEPLOYMENT_REGISTRY
from .exceptions import EntityDoesNotExist, EntityExists
from .operations import delete_parameter, get_parameter, set_parameter
from .project import assert_project_exists
from .utils import aws_client


@feedback
def create_deployment(project, deployment, feedback):
    ssm = aws_client('ssm')
    with feedback(f'Create deployment {colored(project, "cyan")}/{colored(deployment, "green")}'):
        assert_project_exists(project, ssm=ssm)
        name = DEPLOYMENT_REGISTRY.format(project)
        deployments = get_parameter(name, default=[], ssm=ssm)
        if deployment in deployments:
            raise EntityExists
        try:
            deployments.remove('_')
        except ValueError:
            pass
        deployments.append(deployment)
        set_parameter(name, deployments, ssm=ssm)
        # The active flag is here really only to ensure when
        # deployments are carried out for deployments without secrets
        # etc, they are still used.
        name = DEPLOYMENT_PREFIX.format(project, deployment) + 'active'
        set_parameter(name, '1', ssm=ssm)


@feedback
def list_deployments(project, feedback):
    ssm = aws_client('ssm')
    with feedback(f'List deployments for {colored(project, "cyan")}'):
        assert_project_exists(project, ssm=ssm)
        name = DEPLOYMENT_REGISTRY.format(project)
        deployments = get_parameter(name, default=[], ssm=ssm)
        return [d for d in deployments if d != '_']


@feedback
def delete_deployment(project, deployment, feedback):
    ssm = aws_client('ssm')
    with feedback(f'Delete deployment {colored(project, "cyan")}/{colored(deployment, "green")}'):
        assert_project_exists(project, ssm=ssm)
        assert_deployment_exists(project, deployment, ssm=ssm)
        # TODO: Check for related entities?
        name = DEPLOYMENT_REGISTRY.format(project)
        deployments = get_parameter(name, default=[], ssm=ssm)
        deployments.remove(deployment)
        if not deployments:
            deployments.append('_')
        set_parameter(name, deployments, ssm=ssm)
        # TODO: Need to fetch the path, then delete all of them.
        name = DEPLOYMENT_PREFIX.format(project, deployment)
        delete_parameter(name, ssm=ssm)


def deployment_exists(project, deployment, ssm=None):
    registry = get_parameter(DEPLOYMENT_REGISTRY.format(project), ssm=ssm)
    return deployment in registry


def assert_deployment_exists(project, deployment, ssm=None):
    if not deployment_exists(project, deployment, ssm=ssm):
        raise EntityDoesNotExist(
            f'deployment {deployment} does not exist'
        )
