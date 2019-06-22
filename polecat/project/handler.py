class Handler:
    def __init__(self, project, middleware=None):
        self.project = project
        self.middleware = middleware or []

    def prepare(self):
        pass

    def match(self, event):
        return False

    async def run(self, event):
        for mw in self.middleware:
            mw.run(event)
        return await self.handle_event(event)

    async def handle_event(self, event):
        raise NotImplementedError


class HTTPHandler(Handler):
    def match(self, event):
        return event.is_http()
