import os
from pathlib import Path

from termcolor import colored

from ...utils.feedback import feedback
from .exceptions import KnownError
from .operations import get_parameter, set_parameter
from .utils import aws_client


@feedback
def upload(project, bucket, source=None, version=None, feedback=None):
    s3 = aws_client('s3')
    source = Path(source or os.getcwd())
    version_path = f'/polecat/projects/{project}/code/version'  # TODO: Constant.
    current_version = None
    with feedback(f'Prepare version number') as fb:
        current_version = get_parameter(version_path)
        if current_version is not None:
            current_version = int(current_version)
        else:
            current_version = 0
        if version is not None:
            if version > current_version + 1:
                raise KnownError('invalid version provided')
        else:
            version = current_version + 1
        fb.message = f'Using version {colored(version, "blue")}'
    for file in ('server.zip', 'admin.zip'):
        with feedback(f'Upload {colored(file, "blue")}'):
            s3.upload_file(
                str(source / file),
                Bucket=bucket,
                Key=f'projects/{project}/code/{version}/{file}'  # TODO: Constant.
            )
    if version > current_version:
        with feedback(f'Set current version to {colored(version, "blue")}'):
            set_parameter(version_path, str(version))
