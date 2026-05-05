from src.module import foo


def test_foo_1():
    assert foo(1, 2) == 3
    assert foo(0, 0) == 0
