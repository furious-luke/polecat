import os
import shlex
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import click
import ujson

from .main import main

__all__ = ('test_production', 'test_with_pytest')

api_gateway_request = {
    'path': '/graphql',
    'httpMethod': 'GET',
    'headers': {},
    'body': '{}'
}


@main.group()
@click.pass_context
def test(ctx):
    pass


@test.command('production')
@click.argument('source')
@click.pass_context
def test_production(ctx, source):
    with TemporaryDirectory() as root:
        os.chmod(root, 0o755)
        with ZipFile(source, 'r') as zf:
            zf.extractall(root)
        env = {
            'DATABASE_URL': os.environ['DATABASE_URL'],
            'POLECAT_PROJECT_MODULE': 'basic.project.Project'  # TODO
        }
        env_str = ' '.join(f'-e {k}={v}' for k, v in env.items())
        request = api_gateway_request
        cmd = (
            f'docker run --rm -v {root}:/var/task {env_str}'
            f' lambci/lambda:python3.7 main.handler \'{ujson.dumps(request)}\''  # TODO: Escape
        )
        subprocess.call(shlex.split(cmd))


@test.command('pytest')
@click.pass_context
def test_with_pytest(ctx):
    cmd = 'pytest'
    subprocess.call(shlex.split(cmd))
