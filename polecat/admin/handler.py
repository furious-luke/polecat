from ..core.context import active_context
from ..project.handler import Handler


class AdminHandler(Handler):
    def match(self, event):
        return event.is_admin()

    async def handle_event(self, event):
        command = active_context().registries.command_registry[event.event['command']]
        args = event.event['args']
        kwargs = event.event['kwargs']
        command(self.project).run(*args, **kwargs)
