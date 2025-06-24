import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os
from pathlib import Path
import logging
import io
import importlib

def load_utils():
    import logging_utils
    return importlib.reload(logging_utils)


def test_create_success_log(tmp_path):
    utils = load_utils()
    log_file = tmp_path / 'success.md'
    path = utils.create_success_log('All good', output_file=log_file)
    assert Path(path).exists()
    content = Path(path).read_text()
    assert 'KYO QA Tool Success Log' in content


def test_create_failure_log(tmp_path):
    utils = load_utils()
    log_file = tmp_path / 'fail.md'
    path = utils.create_failure_log('oops', 'traceback', output_file=log_file)
    assert Path(path).exists()
    content = Path(path).read_text()
    assert 'KYO QA Tool Failure Log' in content


def test_log_safe_truncates():
    utils = load_utils()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger = logging.getLogger('safe_test')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    long_message = 'A' * 300
    utils.log_safe(logger, long_message, max_length=50)

    handler.flush()
    logged = stream.getvalue().strip()
    assert logged.endswith('...')
    assert len(logged) <= 53
