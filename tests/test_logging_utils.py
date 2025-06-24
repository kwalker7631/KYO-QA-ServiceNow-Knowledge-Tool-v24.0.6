import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pathlib import Path
from logging_utils import create_success_log, create_failure_log


def test_create_success_log(tmp_path):
    log_file = tmp_path / 'success.md'
    path = create_success_log('All good', output_file=log_file)
    assert Path(path).exists()
    content = Path(path).read_text()
    assert 'KYO QA Tool Success Log' in content


def test_create_failure_log(tmp_path):
    log_file = tmp_path / 'fail.md'
    path = create_failure_log('oops', 'traceback', output_file=log_file)
    assert Path(path).exists()
    content = Path(path).read_text()
    assert 'KYO QA Tool Failure Log' in content
