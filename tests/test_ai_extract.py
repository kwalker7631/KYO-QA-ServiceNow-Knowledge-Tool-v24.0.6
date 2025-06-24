import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import types

# Stub out PyMuPDF to avoid heavy dependency
_orig_fitz = sys.modules.get('fitz')
fitz_stub = types.ModuleType('fitz')
class DummyDoc:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass
    @property
    def metadata(self):
        return {}
    def __len__(self):
        return 1
fitz_stub.open = lambda *args, **kwargs: DummyDoc()
sys.modules.setdefault('fitz', fitz_stub)

import ai_extractor

if _orig_fitz is not None:
    sys.modules['fitz'] = _orig_fitz
else:
    del sys.modules['fitz']


def test_ai_extract_basic(monkeypatch, tmp_path):
    text = (
        "Service Bulletin Ref. No. 2M8-0016 (E099)\n"
        "Model: TASKalfa 4000i\n"
        "Subject: Drum issue\n"
        "January 15, 2024"
    )

    # Avoid PDF metadata reading
    monkeypatch.setattr(ai_extractor, 'get_pdf_metadata', lambda p: {'author': 'Kyo Author'})

    pdf = tmp_path / "QA_20146_E099-2M8-0016.pdf"
    pdf.write_text("dummy")

    result = ai_extractor.ai_extract(text, pdf)

    assert result["full_qa_number"] == "2M8-0016"
    assert result["short_qa_number"] == "E099"
    assert result["models"] == "TASKalfa 4000i"
    assert result["subject"] == "Drum issue"
    assert result["published_date"] == "2024-01-15"
    assert result["author"] == "Kyo Author"
