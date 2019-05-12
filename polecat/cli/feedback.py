import sys

from halo import Halo
from termcolor import colored

from ..core.context import active_context
from ..utils.feedback import Feedback


class HaloFeedback(Feedback):
    def __init__(self, message=None):
        ctx = active_context()
        self.spinner = Halo(text=message or '', spinner='dots')
        if message and not ctx.config.debug:
            self.spinner.start()

    def update_message(self, message):
        super().update_message(message)
        ctx = active_context()
        if not self.spinner._spinner_id and not ctx.config.debug:
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
