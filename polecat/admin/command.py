import click

from ..cli.feedback import HaloFeedback
from ..core.registry import Registry, RegistryMetaclass
from ..utils.stringcase import snakecase

Registry('command_registry')


class CommandMetaclass(RegistryMetaclass):
    def __init__(cls, name, bases, dct):
        if not cls.is_baseclass(name, bases):
            command_name = getattr(cls, 'name', snakecase(name))
            cls.name = command_name
        super().__init__(name, bases, dct)
        if not cls.is_baseclass(name, bases):
            from ..cli.admin import admin  # TODO: Ugh.
            params = list(cls().get_params() or ())
            command = click.Command(name=cls.name, params=params, callback=cls._run)
            admin.add_command(command)


class Command(metaclass=CommandMetaclass):
    _registry = 'command_registry'
    _registry_base = 'Command'
    Argument = click.Argument
    Option = click.Option

    def __init__(self, project=None):
        self.project = project

    @classmethod
    def _run(cls, *args, **kwargs):
        ctx = click.get_current_context()
        project = ctx.obj.get('project')
        deployment = ctx.obj.get('deployment')
        # TODO: Support running on all deployments?
        if project and deployment:
            cls._run_remote(project, deployment, *args, **kwargs)
            return
        from ..project.project import load_project  # TODO: Ugh.
        project = load_project()
        project.prepare()  # TODO: Need this?
        command = cls(project)
        command.run(*args, **kwargs)

    @classmethod
    def _run_remote(cls, project, deployment, *args, **kwargs):
        # TODO: Obvs this is too restrictive. We'll need to be able to
        # select the appropriate deployment backend.
        from ..deploy.aws.admin import run_command as aws_run_command
        aws_run_command(project, deployment, cls.name, args, kwargs, feedback=HaloFeedback())

    def get_options(cls):
        pass

    def run(self):
        raise NotImplementedError
