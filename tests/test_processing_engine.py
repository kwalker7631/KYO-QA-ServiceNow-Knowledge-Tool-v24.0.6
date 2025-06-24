import sys
import types
import threading
from pathlib import Path

import fitz
import importlib

# Set up dummy extract.ai_extractor before importing processing_engine
class DummyExtractor:
    def extract(self, text, path):
        return {
            "full_qa_number": "2ND-0001",
            "short_qa_number": "0001",
            "models": "ModelX",
            "subject": "Test",
            "published_date": "2020-01-01",
            "author": "Tester",
        }

extract_pkg = types.ModuleType("extract")
ai_module = types.ModuleType("extract.ai_extractor")
ai_module.QAExtractor = DummyExtractor
extract_pkg.ai_extractor = ai_module
sys.modules.setdefault("extract", extract_pkg)
sys.modules.setdefault("extract.ai_extractor", ai_module)

processing_engine = importlib.import_module("processing_engine")


def _create_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_process_single_pdf(tmp_path):
    pdf = tmp_path / "sample.pdf"
    _create_pdf(pdf, "Hello")
    txt_dir = tmp_path / "txt"
    txt_dir.mkdir()

    progress = []
    ocr_flags = []
    event = threading.Event()

    result = processing_engine.process_single_pdf(
        pdf,
        txt_dir,
        progress.append,
        ocr_flags.append,
        event,
    )

    txt_file = txt_dir / "sample.txt"
    assert txt_file.exists()
    assert ocr_flags == [True, False]
    assert progress == [f"Analyzing content of {pdf.name}..."]
    assert result["file_name"] == "sample.pdf"
    assert result["Meta"] == "ModelX"

