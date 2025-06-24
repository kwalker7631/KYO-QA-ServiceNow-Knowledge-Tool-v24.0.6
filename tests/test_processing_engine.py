import sys
import types
import threading
from pathlib import Path

# Create dummy extract.ai_extractor module so processing_engine can import it
fake_extract = types.ModuleType("ai_extractor")
class DummyQAExtractor:
    def extract(self, text, path):
        return {
            "full_qa_number": "AAA-1234",
            "short_qa_number": "A1234",
            "models": "Model1",
            "subject": "Test subject",
            "published_date": "2024-01-01",
            "author": "Tester",
        }
    def extract_qa_numbers(self, text):
        return []
    def extract_models(self, text):
        return []
    def extract_dates(self, text):
        return []

fake_extract.QAExtractor = DummyQAExtractor
sys.modules['extract.ai_extractor'] = fake_extract

import processing_engine


def test_process_files_with_mock_pdfs(tmp_path, monkeypatch):
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "a.pdf").write_bytes(b"dummy")
    (folder / "b.pdf").write_bytes(b"dummy")

    monkeypatch.setattr(processing_engine, "_is_ocr_needed", lambda p: False)
    monkeypatch.setattr(processing_engine, "extract_text_from_pdf", lambda p: "text")
    monkeypatch.setattr(processing_engine, "qa_extractor", DummyQAExtractor())
    monkeypatch.setattr(processing_engine, "generate_excel", lambda data, out, tpl: str(out))
    monkeypatch.setattr(processing_engine, "get_temp_dir", lambda: tmp_path / "temp")
    monkeypatch.setattr(processing_engine, "cleanup_temp_files", lambda d: None)

    progress_calls = []
    progress_cb = lambda msg: progress_calls.append(msg)
    ocr_cb = lambda state: None
    cancel_event = threading.Event()

    out_excel = tmp_path / "result.xlsx"
    excel_path, review_list, failures = processing_engine.process_files(
        folder, out_excel, None, progress_cb, ocr_cb, cancel_event
    )

    assert excel_path == str(out_excel)
    assert review_list == []
    assert failures == 0
