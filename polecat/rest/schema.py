import re

from .rest_api_context import RestAPIContext


class RestSchema:
    def __init__(self, routes=None):
        self.routes = routes or {}
        self.build()

    def build(self):
        self._ordered_routes = list(reversed(sorted(
            list(self.routes.items()),
            key=lambda x: len(x[0])
        )))
        self._route_prog = re.compile(
            '|'.join(f'({r})' for r, _ in self._ordered_routes)
        )

    def match_view(self, request):
        match = self._route_prog.match(request.path)
        if not match or match.lastindex is None:
            return None
        return self._ordered_routes[match.lastindex - 1][1]


class RestView:
    def __init__(self, field):  # TODO: Bad naming.
        self.field = field

    def resolve(self, request, context_value=None):
        context_value = context_value or {}
        ctx = RestAPIContext(
            self.field,
            context_value.get('event'),
            context_value.get('session')
        )
        # TODO: Must unify this.
        try:
            return self.field.Meta.resolver_manager(ctx)
        except AttributeError:
            return self.field.resolver_manager(ctx)
