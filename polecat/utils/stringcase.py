import re

CAMELCASE_PROG = re.compile(r'_([a-z])')
SNAKECASE_PROG = re.compile(r'([A-Z]+)')


def camelcase(value):
    return (
        value[0].lower() +
        CAMELCASE_PROG.sub(lambda m: m.group(1).upper(), value[1:])
    )


def snakecase(value):
    # TODO: Needs testing.
    def do_sub(m):
        v = m.group(1)
        r = '_' if m.start() else ''
        if len(v) > 1:
            r += v[:-1].lower() + '_' + v[-1].lower()
        else:
            r += v.lower()
        return r
    return SNAKECASE_PROG.sub(do_sub, value)
