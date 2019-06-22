from botocore.exceptions import ClientError, WaiterError

import ujson
from termcolor import colored

from ...utils import get_path, set_path
from ...utils.feedback import feedback
from .constants import PROJECT_PREFIX
from .deployment import assert_deployment_exists
from .exceptions import KnownError
from .operations import get_parameter, get_parameters_by_path
from .resources import (create_api_resources, create_domain_resources,
                        create_output_resources, create_zone_resources)
from .utils import aws_client

# TODO: Need to make the API name dynamic.
api_name = 'Polecat1'


@feedback
def deploy(project, bucket, deployment=None, dry_run=False, feedback=None):
    cf = aws_client('cloudformation')
    msg = f'Deploy {colored(project, "blue")}'
    if deployment:
        msg += f'/{colored(deployment, "green")}'
    with feedback(msg):
        template = create_template(project, bucket, deployment=deployment, cf=cf)
        if dry_run:
            raise Warning('dry run')
        params = {
            'StackName': project,
            'TemplateBody': template,
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
    response = cf.describe_stacks(StackName=project)
    outputs = {}
    for output in response['Stacks'][0]['Outputs']:
        project_deployment = output['OutputKey']
        deployment = project_deployment[len(project):-3].lower()
        url = output['OutputValue']
        outputs[deployment] = url
    return outputs


@feedback
def undeploy(project, deployment=None, feedback=None):
    with feedback(f'Undeploy {colored(project, "blue")}'):
        cf = aws_client('cloudformation')
        cf.delete_stack(StackName=project)
        # TODO: Wait for delete to be finished.
        # TODO: Undeploy individual deployment?


def create_template(project, bucket, deployment=None, cf=None):
    env = get_environment(project, deployment)
    resources, outputs = get_existing_template(project, cf=cf)
    data = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Description': f'Polecat {project} CloudFormation template',
        'Resources': create_resources(project, bucket, env, resources=resources),
        'Outputs': create_outputs(project, env, outputs=outputs)
    }
    return ujson.dumps(data, indent=2)


def get_existing_template(project, cf=None):
    cf = aws_client('cloudformation', client=cf)
    try:
        response = cf.get_template(StackName=project, TemplateStage='Original')
        template = response['TemplateBody']
        return template['Resources'], template['Outputs']
    except ClientError as e:
        if 'does not exist' not in str(e):
            raise
        return {}, {}


def create_resources(project, bucket, environment, resources=None):
    resources = resources or {}
    for dep, env in environment.items():
        resources.update(create_api_resources(project, dep, api_name, bucket, env))
        for domain, info in env.get('domains', {}).items():
            certificate_arn = info['certificate']  # TODO: Confirm it exists?
            resources.update(
                create_domain_resources(project, dep, api_name, domain, certificate_arn)
            )
            zone = info.get('zone', None)
            if zone:
                resources.update(
                    create_zone_resources(project, dep, domain, zone)
                )
    return resources


def create_outputs(project, environment, outputs=None):
    outputs = outputs or {}
    for dep, env in environment.items():
        outputs.update(create_output_resources(project, dep, api_name))
    return outputs


def get_environment(project, deployment=None):
    deployment = deployment or ''
    if deployment:
        assert_deployment_exists(project, deployment)
    prefix = PROJECT_PREFIX.format(project)
    project_code_version = get_parameter(f'{prefix}code/version')  # TODO: Constant.
    if project_code_version is None:
        raise KnownError('No code version available')
    project_bundle_version = get_parameter(f'{prefix}bundle/version', default='')  # TODO: Constant.
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
