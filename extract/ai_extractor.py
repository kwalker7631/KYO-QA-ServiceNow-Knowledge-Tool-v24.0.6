class QAExtractor:
    """Simple extractor stub for local testing."""

    def extract(self, text: str, pdf_path=None) -> dict:
        """Return minimal structured data extracted from text."""
        return {
            "full_qa_number": "",
            "short_qa_number": "",
            "models": "",
            "subject": "",
            "published_date": "",
            "author": "",
        }

    def extract_qa_numbers(self, text: str) -> dict:
        return {
            "full_qa_number": "",
            "short_qa_number": "",
        }

    def extract_models(self, text: str) -> list:
        return []

    def extract_dates(self, text: str) -> list:
        return []
