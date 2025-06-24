import pytest


def test_lambda_captures_exception_message():
    try:
        raise ValueError('boom')
    except Exception as e:
        error_msg = str(e)
        func = lambda m=error_msg: f"CRITICAL ERROR: {m}"
    # 'e' is out of scope here
    assert func() == 'CRITICAL ERROR: boom'
