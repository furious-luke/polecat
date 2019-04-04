from contextlib import contextmanager

import boto3

from .exceptions import EntityExists


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


def default_path(path):
    return path or '/polecat/'
