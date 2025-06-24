from extract.ai_extractor import QAExtractor


def test_create_qa_extractor():
    extractor = QAExtractor()
    assert extractor is not None
