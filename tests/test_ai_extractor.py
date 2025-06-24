from pathlib import Path
from extract.ai_extractor import QAExtractor


def test_basic_extraction():
    extractor = QAExtractor()
    text = (
        "QA notice E014-2LV-0032 for TASKalfa 2554ci "
        "was published on 2024-05-10"
    )
    result = extractor.extract(text, Path("dummy.pdf"))
    assert result["full_qa_number"] == "E014-2LV-0032"
    assert result["short_qa_number"] == "0032"
    assert result["models"] == "TASKalfa 2554ci"
    assert result["published_date"] == "2024-05-10"
