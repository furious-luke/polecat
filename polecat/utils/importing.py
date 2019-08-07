import importlib


def import_attribute(path_or_attr):
    if isinstance(path_or_attr, str):
        last_index = path_or_attr.rfind('.')
        module_path = path_or_attr[:last_index]
        attr_name = path_or_attr[last_index + 1:]
        module = importlib.import_module(module_path)
        path_or_attr = getattr(module, attr_name)
    return path_or_attr
