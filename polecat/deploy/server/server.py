from sanic import Sanic, response

from ...project.project import load_project
from ..event import HttpEvent


class Server:
    def __init__(self, project=None, production=False):
        self.project = project or load_project()
        self.project.prepare()
        self.production = production
        self.port = 80 if production else 8000
        self.sanic_app = Sanic()
        self.sanic_app.add_route(self.index, '/', methods=['GET'])
        self.sanic_app.add_route(
            self.index,
            '/<path:path>',
            methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTION']
        )

    async def index(self, request, path=None):
        return self.encode_result(
            await self.project.handle_event(self.request_to_event(request))
        )

    def request_to_event(self, request):
        return HttpEvent(request)

    def encode_result(self, result):
        return response.json(result[0], status=result[1])

    def run(self):
        self.sanic_app.run(host='0.0.0.0', port=self.port)
