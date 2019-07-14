from polecat.db.schema.variable import SessionVariable
from psycopg2.extensions import AsIs, register_adapter


def adapt_session_variable(sv):
    type = sv.type or ''
    if type:
        # TODO: Should be using a mapping from Python types to DB
        # types.
        type = f'::{type}'
    return AsIs(f"current_setting('{sv.name}', TRUE){type}")


register_adapter(SessionVariable, adapt_session_variable)
