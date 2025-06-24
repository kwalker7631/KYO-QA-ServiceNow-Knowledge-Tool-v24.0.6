import os
import sys
from extract.ai_extractor import QAExtractor

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

SAMPLE_TEXT = """Service Bulletin
Ref. No. 2XD-0052 (M105)
Model: TASKalfa 250ci, TASKalfa 300ci
<Date> January 5, 2023
Subject: Sample subject line
"""

def test_extract_qa_numbers():
    extractor = QAExtractor()
    full_qa, short_qa = extractor.extract_qa_numbers(SAMPLE_TEXT, "QA_M105_2XD_0052_SB.pdf")
    assert full_qa == "2XD-0052"
    assert short_qa == "M105"

def test_extract_models():
    extractor = QAExtractor()
    models = extractor.extract_models(SAMPLE_TEXT, "dummy.pdf")
    assert "TASKalfa 250ci" in models

def test_extract_dates():
    extractor = QAExtractor()
    date = extractor.extract_dates(SAMPLE_TEXT, "dummy.pdf")
    assert date == "2023-01-05"
