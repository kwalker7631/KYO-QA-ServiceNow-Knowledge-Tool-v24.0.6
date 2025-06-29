# flake8: noqa
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_harvesters import harvest_all_data  # noqa: E402


def test_harvest_all_data_basic():
    text = "The QA12345 document covers details."
    result = harvest_all_data(text, "example.pdf")
    assert result["full_qa_number"] == "QA12345"
    assert result["short_qa_number"] == "12345"
