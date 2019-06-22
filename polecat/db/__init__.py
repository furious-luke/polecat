from polecat.core.context import active_context
from polecat.utils.container import Option, OptionDict, passthrough

active_context().Meta.add_options(
    Option('db', default=passthrough(OptionDict)(
        (
            Option('schema'),
        )
    ))
)
