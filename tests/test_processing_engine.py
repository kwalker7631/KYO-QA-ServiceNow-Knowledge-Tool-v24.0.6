import sys
import types
import threading


def test_process_single_pdf(monkeypatch, tmp_path):
    dummy_module = types.ModuleType("extract.ai_extractor")

    class DummyExtractor:
        def extract(self, text, path):
            return {
                "full_qa_number": "2ND-0148",
                "short_qa_number": "E014",
                "models": "ECOSYS P123",
                "subject": "Printer fails to start",
                "published_date": "2024-01-02",
                "author": "Tester",
            }

    dummy_module.QAExtractor = DummyExtractor
    sys.modules["extract"] = types.ModuleType("extract")
    sys.modules["extract.ai_extractor"] = dummy_module

    import importlib
    import processing_engine
    importlib.reload(processing_engine)

    monkeypatch.setattr(processing_engine, "_is_ocr_needed", lambda path: False)
    monkeypatch.setattr(processing_engine, "extract_text_from_pdf", lambda path: "Dummy PDF text")
    monkeypatch.setattr(processing_engine, "save_txt", lambda text, path: None)

    result = processing_engine.process_single_pdf(
        tmp_path / "dummy.pdf",
        tmp_path,
        progress_cb=lambda m: None,
        ocr_cb=lambda b: None,
        cancel_event=threading.Event(),
    )

    assert result["file_name"] == "dummy.pdf"
    for key in ["Meta", "Meta Description", "Short description", "file_name", "needs_review"]:
        assert key in result
