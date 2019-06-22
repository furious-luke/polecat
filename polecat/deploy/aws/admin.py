from base64 import b64decode

import ujson

from ...utils import capitalize
from ...utils.feedback import feedback
from .utils import aws_client


@feedback
def run_command(project, deployment, command, args, kwargs, feedback):
    lmd = aws_client('lambda')
    project_deployment = f'{capitalize(project)}{capitalize(deployment)}'
    payload = ujson.dumps({
        'event': 'admin',
        'command': command,
        'args': args,
        'kwargs': kwargs
    }).encode()
    response = lmd.invoke(
        FunctionName=f'{project_deployment}Server',
        LogType='Tail',
        Payload=payload
    )
    logs = response.get('LogResult')
    if logs:
        # TODO: Move to somewhere better.
        logs = b64decode(logs)
        logs = logs.replace(b'\r\xc2\xa0\xc2\xa0', b'\n')
        print(logs.decode())
