from polecat import model

__all__ = ('Contact',)


class Contact(model.Model):
    name = model.TextField()
