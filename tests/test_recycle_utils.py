from recycle_utils import apply_recycles

def test_apply_recycles_basic():
    rules = [(r"foo", "bar")]
    result = apply_recycles("foo test", rules)
    assert "bar" in result and "foo" not in result
