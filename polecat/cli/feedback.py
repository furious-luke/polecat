import sys

from halo import Halo
from termcolor import colored

from ..utils.feedback import Feedback


class HaloFeedback(Feedback):
    def __init__(self, message=None):
        self.spinner = Halo(text=message or '', spinner='dots')
        if message:
            self.spinner.start()

    def update_message(self, message):
        super().update_message(message)
        if not self.spinner._spinner_id:
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

    def exists(self):
        self.warning('exists')
