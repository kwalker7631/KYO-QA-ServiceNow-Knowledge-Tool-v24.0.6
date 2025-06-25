import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_harvesters import bulletproof_extraction


def test_bulletproof_extraction_basic():
    text = "This doc E1234-ABCD-001 covers details."
    result = bulletproof_extraction(text, "example.pdf")
    assert result["full_qa_number"] == "E1234-ABCD-001"
    assert result["short_qa_number"] == "E1234"
