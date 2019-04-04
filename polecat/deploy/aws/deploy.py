import ujson
from botocore.exceptions import ClientError, WaiterError
from termcolor import colored

from ...utils import get_path, set_path
from ...utils.feedback import feedback
from .exceptions import KnownError
from .operations import get_parameter, get_parameters_by_path
from .resources import (create_api_resources, create_domain_resources,
                        create_output_resources, create_zone_resources)
from .utils import aws_client


@feedback
def deploy(project, bucket, deployment=None, feedback=None):
    cf = aws_client('cloudformation')
    with feedback(f'Deploy {colored(project, "blue")}'):
        params = {
            'StackName': project,
            'TemplateBody': create_template(project, bucket, deployment),
            'Capabilities': ['CAPABILITY_IAM']
        }
        wait_command = 'stack_update_complete'
        try:
            cf.update_stack(**params)
        except ClientError as e:
            if 'No updates are to be performed' in str(e):
                raise Warning('no changes detected')
            elif 'does not exist' not in str(e):
                raise
            wait_command = 'stack_create_complete'
            cf.create_stack(**params)
        waiter = cf.get_waiter(wait_command)
        try:
            waiter.wait(StackName=project)
        except WaiterError:
            raise KnownError('failed')


@feedback
def undeploy(project, deployment):
    pass
    #     const app = getConfig('app')
    # await loggedOperation(`Undeploying ${app.blue} ... `, async () => {
    #   const cf = new AWS.CloudFormation()
    #   const response = await cf.deleteStack({
    #     StackName: app
    #   }).promise()
    # })


def create_template(project, bucket, deployment=None):
    env = get_environment(project, deployment)
    data = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Description': f'Polecat {project} CloudFormation template',
        'Resources': create_resources(project, bucket, env),
        'Outputs': create_outputs(project, env)
    }
    return ujson.dumps(data, indent=2)


def create_resources(project, bucket, environment):
    resources = {}
    for dep, env in environment.items():
        resources.update(create_api_resources(project, dep, bucket, env))
        for domain, info in env.get('domains', {}).items():
            certificate_arn = info['certificate']  # TODO: Confirm it exists?
            resources.update(
                create_domain_resources(project, dep, domain, certificate_arn)
            )
            zone = info.get('zone', None)
            if zone:
                resources.update(
                    create_zone_resources(project, dep, domain, zone)
                )
    return resources


def create_outputs(project, environment):
    outputs = {}
    for dep, env in environment.items():
        outputs.update(create_output_resources(project, dep))
    return outputs


def get_environment(project, deployment=None):
    deployment = deployment or ''
    prefix = f'/polecat/projects/{project}'  # TODO: Constant.
    project_code_version = get_parameter(f'{prefix}/code/version')  # TODO: Constant.
    if project_code_version is None:
        raise KnownError('No code version available')
    project_bundle_version = get_parameter(f'{prefix}/bundle/version', default='')  # TODO: Constant.
    path = f'/polecat/projects/{project}/deployments/{deployment}' + ('/' if deployment else '')
    environment = get_parameters_by_path(path)
    if deployment:
        environment = {
            deployment: environment
        }
    if project_code_version:
        for dep, env in environment.items():
            if get_path(env, 'code.version') is None:
                set_path(env, 'code.version', project_code_version)
            if get_path(env, 'bundle.version') is None:
                set_path(env, 'bundle.version', project_bundle_version)
    return environment
