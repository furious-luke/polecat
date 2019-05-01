from ..project.handler import Handler
from .command import command_registry


class AdminHandler(Handler):
    def match(self, event):
        return event.is_admin()

    async def handle_event(self, event):
        command = command_registry.map(event.event['command'])
        args = event.event['args']
        kwargs = event.event['kwargs']
        command().run(*args, **kwargs)
