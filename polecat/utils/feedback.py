from functools import wraps

from .exceptions import EntityDoesNotExist, EntityExists, KnownError


class Feedback:
    def __call__(self, message=None):
        self.update_message(message)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            if exc_type == EntityExists:
                self.exists(exc_value)
                return True
            elif exc_type == EntityDoesNotExist:
                self.errored(exc_value)
                return True
            elif exc_type == Warning:
                self.warning(exc_value)
                return True
            elif exc_type == KnownError:
                self.errored(exc_value)
                return True
        else:
            self.succeeded()

    def update_message(self, message):
        self.message = message or ''

    def errored(self, error):
        pass

    def succeeded(self):
        pass

    def warning(self, warning):
        pass

    def info(self, message):
        pass

    def exists(self, error):
        pass


def feedback(func):
    @wraps(func)
    def inner(*args, feedback=None, **kwargs):
        if feedback is None:
            fb = Feedback()
            return func(*args, feedback=fb, **kwargs)
        else:
            return func(*args, feedback=feedback, **kwargs)
    return inner
