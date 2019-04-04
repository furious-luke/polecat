from polecat.utils.stringcase import snakecase


def test_snakecase():
    assert snakecase('helloWorld') == 'hello_world'
