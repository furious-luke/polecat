from termcolor import colored

from ...utils.feedback import feedback
from .constants import SECRET_NAME, SECRET_PREFIX
from .operations import delete_parameter, get_parameters_by_path, set_parameter
from .utils import aws_client


@feedback
def create_secret(project, deployment, key, value, feedback):
    ssm = aws_client('ssm')
    with feedback(f'Create secret {colored(key, "cyan")} for {colored(project, "blue")}/{colored(deployment, "green")}'):
        name = SECRET_NAME.format(project, deployment, key)
        set_parameter(name, value, ssm=ssm)


@feedback
def list_secrets(project, deployment, feedback):
    ssm = aws_client('ssm')
    with feedback(f'List secrets for {colored(project, "blue")}/{colored(deployment, "green")}'):
        prefix = SECRET_PREFIX.format(project, deployment)
        return get_parameters_by_path(prefix, ssm=ssm)


@feedback
def delete_secret(project, deployment, key, feedback):
    ssm = aws_client('ssm')
    with feedback(f'Delete secret {colored(key, "cyan")} for {colored(project, "blue")}/{colored(deployment, "green")}'):
        name = SECRET_NAME.format(project, deployment, key)
        delete_parameter(name, ssm=ssm)
