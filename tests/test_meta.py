from polecat.utils.meta import Meta
from polecat.utils.optiondict import Option


def define_meta():
    class TestMeta(Meta):
        an_int = int
        a_list = list
        with_default = (int, 1)
        an_option = Option(default='a')
    return TestMeta()


def test_define():
    meta = define_meta()
    assert meta.with_default == 1
    assert meta.an_option == 'a'


def test_distinct():
    meta0 = define_meta()
    meta1 = define_meta()
    meta0.an_int = 1
    meta1.an_int = 2
    assert meta0.an_int == 1
    assert meta1.an_int == 2


def test_merge_from_type():
    meta = define_meta()
    meta.a_list = [2]
    type_to_merge = type('TestType', (), {
        'an_int': 1,
        'a_list': 3
    })
    meta.Meta.merge_from_type(type_to_merge)
    assert meta.an_int == 1
    assert meta.a_list == [2, 3]
