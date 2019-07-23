import click
from termcolor import colored

from .config import update_config
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
    update_config({'project': project})


@project.command('list')
def list_projects():
    from ..deploy.aws.project import list_projects as aws_list_projects
    projects = aws_list_projects(feedback=HaloFeedback())
    if len(projects) == 0:
        print(colored('    No projects', 'grey'))
    else:
        for proj in projects:
            print(f'    {proj}')


@project.command('delete')
@click.argument('project')
@click.pass_context
def delete_project(ctx, project):
    from ..deploy.aws.project import delete_project as aws_delete_project
    aws_delete_project(project, feedback=HaloFeedback())
    update_config(delete=['project'])
