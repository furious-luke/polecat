from contextlib import contextmanager

import boto3

from .exceptions import EntityDoesNotExist, EntityExists


def aws_client(service, client=None, region=None):
    return client or boto3.client(service, region_name=region)


def aws_resource(service, resource=None):
    return resource or boto3.resource(service)


@contextmanager
def aws_exists():
    try:
        yield
    except Exception as e:
        try:
            code = e.response['Error']['Code']
        except (KeyError, AttributeError):
            code = None
        if code in ('EntityAlreadyExists', 'BucketAlreadyOwnedByYou',
                    'BucketPolicyAlreadyExists', 'ParameterAlreadyExists'):
            raise EntityExists
        raise


@contextmanager
def aws_does_not_exist(swallow=False):
    try:
        yield
    except Exception as e:
        try:
            code = e.response['Error']['Code']
        except (KeyError, AttributeError):
            code = None
        if code in ('DBInstanceNotFound',):
            if not swallow:
                raise EntityDoesNotExist
        else:
            raise


def default_path(path):
    return path or '/polecat/'


def assert_project_and_deployment_exists(project, deployment, ssm=None):
    from .project import assert_project_exists
    from .deployment import assert_deployment_exists
    assert_project_exists(project, ssm=ssm)
    assert_deployment_exists(deployment, ssm=ssm)
