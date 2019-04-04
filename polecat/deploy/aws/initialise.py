from termcolor import colored

from ...utils.feedback import feedback
from .constants import POLECAT_ADMINISTRATOR, POLECAT_BASE, PROJECT_REGISTRY
from .exceptions import EntityExists
from .operations import (add_user_to_group, attach_bucket_policy,
                         attach_group_policy, create_bucket, create_group,
                         create_policy, create_user, find_policy,
                         get_parameter, set_parameter)
from .policy import administrator_policy, base_policy, bucket_policy
from .utils import aws_client


@feedback
def initialise(bucket, feedback):
    iam = aws_client('iam')
    s3 = aws_client('s3')
    ssm = aws_client('ssm')
    with feedback(f'Create bucket {colored(bucket, "cyan")}'):
        create_bucket(bucket, s3=s3)
    with feedback('Attach bucket policy'):
        attach_bucket_policy(bucket, bucket_policy, s3=s3)
    with feedback('Create base policy'):
        create_base_policy(iam=iam)
    with feedback('Create administrator policy'):
        create_administrator_policy(iam=iam)
    with feedback('Create administrator group'):
        create_administrator_group(iam=iam)
    with feedback('Attach administrator policy'):
        attach_administrator_policies(iam=iam)
    with feedback('Create administrator user'):
        create_administrator_user(iam=iam)
    with feedback('Attach administrator group'):
        attach_administrator_group(iam=iam)
    with feedback('Create project registry'):
        create_project_registry(ssm=ssm)


def create_base_policy(iam=None):
    create_policy(POLECAT_BASE, base_policy, iam=iam)


def create_administrator_policy(iam=None):
    create_policy(POLECAT_ADMINISTRATOR, administrator_policy)


def create_administrator_group(iam=None):
    create_group(POLECAT_ADMINISTRATOR, iam=iam)


def attach_administrator_policies(iam=None):
    attach_group_policy(
        POLECAT_ADMINISTRATOR,
        find_policy(POLECAT_BASE).arn
    )
    attach_group_policy(
        POLECAT_ADMINISTRATOR,
        find_policy(POLECAT_ADMINISTRATOR).arn
    )


def create_administrator_user(iam=None):
    access_key = create_user(POLECAT_ADMINISTRATOR, iam=iam)
    if access_key:
        # TODO: Convert
        # console.info('\nA new administrator user has been created. Please')
        # console.info('access Polecat using the following keys:\n')
        # console.info(`  AWS_ACCESS_KEY_ID = ${adminUser.AccessKeyId}`)
        # console.info(`  AWS_ACCESS_KEY_ID = ${adminUser.SecretAccessKey}\n`)
        pass


def attach_administrator_group(iam=None):
    add_user_to_group(POLECAT_ADMINISTRATOR, POLECAT_ADMINISTRATOR)


def create_project_registry(ssm=None):
    if get_parameter(PROJECT_REGISTRY, ssm=ssm) is not None:
        raise EntityExists
    set_parameter(PROJECT_REGISTRY, ['_'], ssm=ssm)
