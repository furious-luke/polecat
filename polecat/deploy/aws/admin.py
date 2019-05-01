import ujson

from ...utils import capitalize
from ...utils.feedback import feedback
from .utils import aws_client


@feedback
def run_command(project, deployment, args, kwargs, feedback):
    lmd = aws_client('lambda')
    project_deployment = f'{project}{capitalize(deployment)}'
    payload = ujson.dumps({
        'event': 'admin',
        'args': args,
        'kwargs': kwargs
    }).encode()
    lmd.invoke(
        FunctionName=project_deployment,
        LogType='Tail',
        Payload=payload
    )
