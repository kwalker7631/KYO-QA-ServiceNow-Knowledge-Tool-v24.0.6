import sys
import types
import fitz
from pathlib import Path

extract_module = types.ModuleType("extract.ai_extractor")
class DummyExtractor:
    def extract(self, text, path):
        return {}
extract_module.QAExtractor = DummyExtractor
sys.modules['extract'] = types.ModuleType('extract')
sys.modules['extract.ai_extractor'] = extract_module

from processing_engine import _is_ocr_needed


def test_is_ocr_needed_returns_false(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    text = "A" * 500
    for i in range(4):
        page.insert_text((72, 72 + i * 28), text)
    doc.save(pdf_path)
    doc.close()

    assert _is_ocr_needed(pdf_path) is False
