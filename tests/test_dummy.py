from pyshapes.dummy import multiply

def test_dummy_test():
    assert multiply(3, 4) == 12
    assert multiply(3, 4, 5) == 60
