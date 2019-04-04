import click
from termcolor import colored

from .feedback import HaloFeedback
from .main import main

__all__ = ('create_project', 'list_projects')


@main.group()
@click.pass_context
def project(ctx):
    pass


@project.command('create')
@click.argument('project')
@click.pass_context
def create_project(ctx, project):
    from ..deploy.aws.project import create_project as aws_create_project
    bucket = ctx.obj['bucket']
    aws_create_project(project, bucket, feedback=HaloFeedback())


@project.command('list')
def list_projects():
    from ..deploy.aws.project import list_projects as aws_list_projects
    projects = aws_list_projects(feedback=HaloFeedback())
    if len(projects) == 0:
        print(colored('    No projects', 'grey'))
    else:
        for proj in projects:
            print(f'    {proj}')
