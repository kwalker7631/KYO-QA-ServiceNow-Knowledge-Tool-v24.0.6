"""Simple QA extractor for KYO QA ServiceNow tool."""
import re
from pathlib import Path
from logging_utils import setup_logger


class QAExtractor:
    """Parse text for QA numbers, model names, and dates."""

    def __init__(self):
        self.logger = setup_logger("qa_extractor")

    def extract_qa_numbers(self, text: str) -> dict:
        """Return full and short QA numbers if found."""
        full_match = re.search(r"[A-Z0-9]{3,4}-[A-Z0-9]{2,3}-\d{4}", text)
        full = full_match.group(0) if full_match else ""
        short_match = re.search(r"(\d{4})", full)
        short = short_match.group(1) if short_match else ""
        return {"full_qa_number": full, "short_qa_number": short}

    def extract_models(self, text: str) -> str:
        """Return the first matched model name."""
        match = re.search(r"(TASKalfa|ECOSYS)\s?[A-Za-z0-9]+", text)
        return match.group(0) if match else ""

    def extract_dates(self, text: str) -> str:
        """Return the first YYYY-MM-DD date found."""
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        return match.group(0) if match else ""

    def extract(self, text: str, pdf_path: Path) -> dict:
        """High level extraction routine."""
        numbers = self.extract_qa_numbers(text)
        return {
            "full_qa_number": numbers.get("full_qa_number", ""),
            "short_qa_number": numbers.get("short_qa_number", ""),
            "models": self.extract_models(text),
            "subject": "",
            "published_date": self.extract_dates(text),
            "author": "",
            "document_type": "HTML",
            "file_path": str(pdf_path),
        }
