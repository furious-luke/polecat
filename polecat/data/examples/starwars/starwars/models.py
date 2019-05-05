from polecat import model


class Film(model.Model):
    title = model.TextField(null=False)


class Planet(model.Model):
    name = model.TextField(null=False)
    film = model.RelatedField(Film)


class Character(model.Model):
    name = model.TextField(null=False)
    film = model.RelatedField(Film)
