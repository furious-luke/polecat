from polecat import model


def build_test_model(field_hook=None):
    class TestModel(model.Model):
        field = model.IntField(hooks=field_hook)
    return TestModel


def test_field_hook(push_blueprint):
    called = 0

    def test_field_hook(blueprint):
        nonlocal called
        called += 1

    build_test_model(field_hook=test_field_hook)
    push_blueprint.run_hooks()
    assert called == 1
