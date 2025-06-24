import os
import sys
import types
import fitz
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Stub out extract.ai_extractor to avoid heavy imports
extract = types.ModuleType("extract")
extract.ai_extractor = types.ModuleType("ai_extractor")
extract.ai_extractor.QAExtractor = object
sys.modules.setdefault("extract", extract)
sys.modules.setdefault("extract.ai_extractor", extract.ai_extractor)

from processing_engine import _is_ocr_needed

def create_two_page_pdf(tmp_path: Path) -> Path:
    doc = fitz.open()
    doc.new_page()  # first page blank
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Text on page 2")
    pdf_path = tmp_path / "sample.pdf"
    doc.save(pdf_path)
    doc.close()
    return pdf_path

def test_is_ocr_needed_first_page_only(tmp_path):
    pdf_file = create_two_page_pdf(tmp_path)
    assert _is_ocr_needed(pdf_file)
