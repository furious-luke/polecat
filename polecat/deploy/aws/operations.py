import os

from botocore.exceptions import ClientError

from ...utils import set_path, substitute
from .exceptions import EntityDoesNotExist
from .utils import (aws_client, aws_does_not_exist, aws_exists, aws_resource,
                    default_path)


def create_policy(name, document, path=None, iam=None):
    iam = aws_client('iam', iam)
    with aws_exists():
        iam.create_policy(
            PolicyName=name,
            Path=default_path(path),
            PolicyDocument=document
        )


def delete_policy(name, iam=None):
    iam = aws_client('iam', iam)
    with aws_does_not_exist():
        arn = find_policy(name).arn
        iam.delete_policy(PolicyArn=arn)


def create_group(name, path=None, iam=None):
    iam = aws_client('iam', iam)
    with aws_exists():
        iam.create_group(
            GroupName=name,
            Path=default_path(path)
        )


def delete_group(name, iam=None):
    iam = aws_client('iam', iam)
    with aws_does_not_exist():
        iam.delete_group(GroupName=name)


def attach_group_policy(group_name, policy_arn, iam=None):
    iam = aws_client('iam', iam)
    with aws_exists():
        iam.attach_group_policy(
            GroupName=group_name,
            PolicyArn=policy_arn
        )


def detach_group_policy(group_name, policy_arn, iam=None):
    iam = aws_client('iam', iam)
    with aws_does_not_exist():
        iam.detach_group_policy(
            GroupName=group_name,
            PolicyArn=policy_arn
        )


def find_policy(name, iam=None):
    iam = aws_resource('iam', iam)
    for policy in iam.policies.filter():
        if policy.policy_name == name:
            return policy
    raise EntityDoesNotExist


def create_user(name, path=None, iam=None):
    iam = aws_client('iam', iam)
    with aws_exists():
        iam.create_user(
            UserName=name,
            Path=default_path(path)
        )
        response = iam.create_access_key(
            UserName=name
        )
        return response['AccessKey']


def add_user_to_group(user_name, group_name, iam=None):
    iam = aws_client('iam', iam)
    with aws_exists():
        iam.add_user_to_group(
            UserName=user_name,
            GroupName=group_name
        )


def create_bucket(name, s3=None):
    s3 = aws_client('s3', s3)
    with aws_exists():
        s3.create_bucket(
            Bucket=name,
            CreateBucketConfiguration={
                'LocationConstraint': os.environ['AWS_DEFAULT_REGION']
            }
        )


def attach_bucket_policy(bucket, policy, s3=None):
    s3 = aws_client('s3', s3)
    with aws_exists():
        s3.put_bucket_policy(
            Bucket=bucket,
            Policy=substitute(policy, bucket=bucket)
        )


def set_parameter(key, value, ssm=None):
    ssm = aws_client('ssm', ssm)
    if isinstance(value, (list, tuple)):
        type = 'StringList'
        value = ','.join(value)
    else:
        type = 'String'
    with aws_exists():
        ssm.put_parameter(
            Name=key,
            Type=type,
            Value=value,
            Overwrite=True
        )


def get_parameter(key, default=None, ssm=None):
    ssm = aws_client('ssm', ssm)
    try:
        response = ssm.get_parameter(Name=key)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            return default
        raise
    param = response['Parameter']
    value = param['Value']
    if param['Type'] == 'StringList':
        value = value.split(',')
    return value


def get_parameters_by_path(path, ssm=None):
    if path[-1] != '/':
        raise ValueError('path must end in /')
    ssm = aws_client('ssm', ssm)
    try:
        response = ssm.get_parameters_by_path(Path=path, Recursive=True)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            raise EntityDoesNotExist
        raise
    params = {}
    for param in response['Parameters']:
        set_path(params, param['Name'][len(path):], param['Value'], '/')
    return params


def delete_parameter(key, ssm=None):
    ssm = aws_client('ssm', ssm)
    try:
        if isinstance(key, (list, tuple)):
            ssm.delete_parameters(Names=key)
        else:
            ssm.delete_parameter(Name=key)
    except ClientError as e:
        if e.response['Error']['Code'] != 'ParameterNotFound':
            raise
