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
            version = int(version)
            if version > current_version + 1:
                raise KnownError('invalid version provided')
        else:
            version = current_version + 1
        fb.message = f'Using version {colored(version, "blue")}'
    for file in ('server.zip',):  # 'admin.zip'):
        with feedback(f'Upload {colored(file, "blue")}'):
            s3.upload_file(
                str(source / file),
                Bucket=bucket,
                Key=f'projects/{project}/code/{version}/{file}'  # TODO: Constant.
            )
    if version > current_version:
        with feedback(f'Set current version to {colored(version, "blue")}'):
            set_parameter(version_path, str(version))


@feedback
def upload_bundle(project, bucket, source=None, version=None, feedback=None):
    s3 = aws_client('s3')
    source = Path(source or (Path(os.getcwd()) / 'dist'))
    def _upload(path, dst_file):
        params = {}
        if '.map.' in dst_file or dst_file.endswith('.map'):
            return
        # TODO: Should really generalize this.
        if dst_file.endswith('stats.json'):
            return
        if dst_file.endswith('.br'):
            return
        if dst_file.endswith('.gz'):
            params['ExtraArgs'] = {
                'ContentEncoding': 'gzip'
            }
        with feedback(f'Upload {colored(dst_file, "blue")}'):
            s3.upload_file(
                path,
                Bucket=bucket,
                Key=f'projects/{project}/bundle/{version}/{dst_file}',  # TODO: Constant.
                **params
            )
        uploaded.append(dst_file)
    # TODO: This is duplication of above.
    version_path = f'/polecat/projects/{project}/bundle/version'  # TODO: Constant.
    current_version = None
    with feedback(f'Prepare version number') as fb:
        current_version = get_parameter(version_path)
        if current_version is not None:
            current_version = int(current_version)
        else:
            current_version = 0
        if version is not None:
            version = int(version)
            if version > current_version + 1:
                raise KnownError('invalid version provided')
        else:
            version = current_version + 1
        fb.message = f'Using version {colored(version, "blue")}'
    uploaded = []
    if source.is_file():
        _upload(str(source), source.name)
    for root, dirs, files in os.walk(source):
        for file in files:
            # TODO: Filter out certain files?
            path = str(Path(root, file))
            dst_file = path[len(str(source)):]
            if dst_file[0] == '/':
                dst_file = dst_file[1:]
            _upload(path, dst_file)
    # TODO: Duplication of above.
    if version > current_version:
        with feedback(f'Set current version to {colored(version, "blue")}'):
            if not len(uploaded):
                raise KnownError('no files uploaded')
            set_parameter(version_path, str(version))
