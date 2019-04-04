from graphql import graphql_sync


def execute_query(schema, query, variables=None, reraise=False):
    result = graphql_sync(schema, query, variable_values=variables)
    if reraise and result.errors:
        raise result.errors[0]
    return result
