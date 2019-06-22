import re


class DevelopMiddleware:
    host_prog = re.compile(r'[a-zA-Z0-9._-]+\.amazonaws\.com')

    def run(self, event, context=None):
        match = self.host_prog.match(event.request.host or '')
        if match:
            if event.request.path:
                ii = 0
                if event.request.path[0] == '/':
                    ii += 1
                ii = event.request.path.find('/', ii)
                event.request.path = event.request.path[ii:]
