import sys
from functools import wraps

from halo import Halo
from polecat.core.config import default_config
from polecat_feedback.decorators import feedback
from polecat_feedback.renderer import Renderer
from termcolor import colored

from ..utils.feedback import Feedback


def cli_feedback(title):
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            ctx = args[0]
            renderer = Renderer(max_width=88)
            with feedback(title, app_name='Polecat', version='v0.0.8', renderer=renderer) as fb:
                path = ctx.obj.get('config_path')
                if path:
                    # TODO: Should be hiding this.
                    path = fb.renderer.t.bright_white(path)
                    fb.add_notice(f'Loaded configuration from {path}')
                try:
                    return func(*args, feedback=fb, **kwargs)
                except Exception as e:
                    # TODO: Add error handling.
                    raise
        return inner
    return outer


class HaloFeedback(Feedback):
    def __init__(self, message=None):
        self.spinner = Halo(text=message or '', spinner='dots')
        if message and not default_config.debug:
            self.spinner.start()

    def update_message(self, message):
        super().update_message(message)
        if not self.spinner._spinner_id and not default_config.debug:
            self.spinner.start()
        self.spinner.text = (message + ' ...') if self.message else ''

    def succeeded(self):
        self.spinner.text = self.message
        self.spinner.succeed()

    def errored(self, error):
        # self.spinner.text = str(error) if error else self.message
        self.spinner.text = f'{self.message} ... {colored(str(error), "red")}'
        self.spinner.fail()
        sys.exit(1)

    def warning(self, warning):
        self.spinner.text = f'{self.message} ... {colored(str(warning), "yellow")}'
        self.spinner.warn()

    def info(self, message):
        self.spinner.info(message)

    def exists(self, error):
        self.warning('exists')
