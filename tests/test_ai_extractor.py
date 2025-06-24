import os
import types
import sys

# Stub out heavy dependencies before importing the module under test
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

sys.modules['ocr_utils'] = types.SimpleNamespace(get_pdf_metadata=lambda x: {})
sys.modules['data_harvesters'] = types.SimpleNamespace(identify_document_type=lambda x: '')
sys.modules['logging_utils'] = types.SimpleNamespace(
    setup_logger=lambda name: None,
    log_info=lambda *args, **kwargs: None,
    log_error=lambda *args, **kwargs: None,
    log_warning=lambda *args, **kwargs: None,
)
sys.modules['config'] = types.SimpleNamespace(STANDARDIZATION_RULES={"default_author": ""})

from ai_extractor import extract_qa_numbers, extract_models, extract_dates

SAMPLE_TEXT = """
Service Bulletin
Ref. No. 2XD-0052 (M105)
Model: TASKalfa 250ci, TASKalfa 300ci
<Date> January 5, 2023
Subject: Sample subject line
"""


def test_extract_qa_numbers():
    full_qa, short_qa = extract_qa_numbers(SAMPLE_TEXT, "QA_M105_2XD_0052_SB.pdf")
    assert full_qa == "2XD-0052"
    assert short_qa == "M105"


def test_extract_models():
    models = extract_models(SAMPLE_TEXT, "dummy.pdf")
    assert "TASKalfa 250ci" in models


def test_extract_dates():
    date = extract_dates(SAMPLE_TEXT, "dummy.pdf")
    assert date == "2023-01-05"
