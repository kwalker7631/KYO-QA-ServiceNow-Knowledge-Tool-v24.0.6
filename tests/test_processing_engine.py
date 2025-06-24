# ruff: noqa: E402
import os
import sys
import types
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Provide dummy extract.ai_extractor for module import
ai_mod = types.ModuleType("extract.ai_extractor")
class DummyExtractor:
    def extract(self, text, path):
        return {}
    def extract_qa_numbers(self, text):
        return []
    def extract_models(self, text):
        return []
    def extract_dates(self, text):
        return []

ai_mod.QAExtractor = DummyExtractor
sys.modules["extract.ai_extractor"] = ai_mod
sys.modules["extract"] = types.ModuleType("extract")
sys.modules["extract"].ai_extractor = ai_mod

import openpyxl
import processing_engine
from logging_utils import LOG_DIR


def test_process_files_generates_excel_and_review_list(tmp_path, mocker):
    # Create dummy PDF files
    pdf1 = tmp_path / "first.pdf"
    pdf1.write_text("dummy")
    pdf2 = tmp_path / "second.pdf"
    pdf2.write_text("dummy")

    excel_out = tmp_path / "out.xlsx"
    cancel_event = threading.Event()

    # Mock OCR checks and text extraction
    mocker.patch("processing_engine._is_ocr_needed", return_value=False)
    mocker.patch("processing_engine.extract_text_from_pdf", return_value="text")

    # Mock AI extractor to return one record needing review and one clean
    mocker.patch(
        "processing_engine.qa_extractor.extract",
        side_effect=[
            {
                "full_qa_number": "QA-0001",
                "short_qa_number": "0001",
                "models": "",  # triggers review
                "subject": "Subject one",
                "published_date": "2024-01-01",
                "author": "tester",
            },
            {
                "full_qa_number": "QA-0002",
                "short_qa_number": "0002",
                "models": "ModelX",
                "subject": "Subject two",
                "published_date": "2024-01-01",
                "author": "tester",
            },
        ],
    )

    final_path, review_list, failed = processing_engine.process_files(
        tmp_path, excel_out, None, lambda *_: None, lambda *_: None, cancel_event
    )

    assert Path(final_path) == excel_out
    assert excel_out.exists()
    wb = openpyxl.load_workbook(excel_out)
    assert wb.active.max_row >= 3  # header + two rows
    assert failed == 0
    assert review_list == ["first.pdf"]

    log_file = LOG_DIR / f"{datetime.now():%Y%m%d}_processing_engine.log"
    assert log_file.exists()
