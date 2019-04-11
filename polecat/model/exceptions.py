class InvalidFieldError(Exception):
    def __init__(self, model, field_name):
        super().__init__(f'{model.Meta.name} has no field "{field_name}"')


class InvalidModelDataError(Exception):
    def __init__(self, model, data):
        super().__init__(f'data type {type(data)} invalid for {model.Meta.name}')
