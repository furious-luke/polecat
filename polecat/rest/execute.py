from graphql_server.error import HttpQueryError


async def run_http_query(schema, request, context_value=None):
    view = schema.match_view(request)
    if not view:
        raise HttpQueryError(404, 'Not found')
    return (
        view.resolve(request, context_value=context_value),
        200
    )
