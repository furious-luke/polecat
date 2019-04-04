def strip_default(type):
    if type.startswith('default:'):
        type = type[8:]
    return type
