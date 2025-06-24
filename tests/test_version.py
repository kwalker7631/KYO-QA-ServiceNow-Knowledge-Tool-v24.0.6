from version import get_version

def test_get_version():
    assert get_version() == "24.0.6"
