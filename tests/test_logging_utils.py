import logging_utils
from pathlib import Path


def test_setup_logger_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_utils, "LOG_DIR", tmp_path)
    logger = logging_utils.setup_logger("unit_test", console_output=False)
    logger.info("hello")
    for h in logger.handlers:
        h.flush()
    files = list(tmp_path.glob("*_unit_test.log"))
    assert files
    content = files[0].read_text(encoding="utf-8")
    assert "hello" in content
