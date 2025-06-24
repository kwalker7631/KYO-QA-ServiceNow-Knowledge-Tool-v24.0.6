import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import extract.ai_extractor as ai_extractor
from extract.ai_extractor import QAExtractor


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

    extractor = QAExtractor()
    result = extractor.extract(text, pdf)

    assert result["full_qa_number"] == "2M8-0016"
    assert result["short_qa_number"] == "E099"
    assert result["models"] == "TASKalfa 4000i"
    assert result["subject"] == "Drum issue"
    assert result["published_date"] == "2024-01-15"
    assert result["author"] == "Kyo Author"
