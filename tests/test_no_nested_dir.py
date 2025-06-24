import os


def test_no_inner_directory():
    assert not os.path.isdir('KYO-QA-ServiceNow-Knowledge-Tool-v24.0.6')
