import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from excel_generator import sanitize_for_excel, MAX_EXCEL_CELL_LENGTH


def test_sanitize_truncates_long_strings():
    long_value = "A" * (MAX_EXCEL_CELL_LENGTH + 10)
    result = sanitize_for_excel(long_value)
    assert len(result) == MAX_EXCEL_CELL_LENGTH
