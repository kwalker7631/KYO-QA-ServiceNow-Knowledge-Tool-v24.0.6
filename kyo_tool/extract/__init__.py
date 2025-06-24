"""Lightweight wrapper around the external ``extract`` package.

This exposes a simple API so other modules can call
``kyo_tool.extract.ai_extract`` without caring about the underlying
implementation.
"""

from extract.ai_extractor import QAExtractor  # type: ignore

_extractor = QAExtractor()

ai_extract = _extractor.extract
extract_qa_numbers = _extractor.extract_qa_numbers
extract_models = _extractor.extract_models
extract_dates = _extractor.extract_dates

__all__ = [
    "QAExtractor",
    "ai_extract",
    "extract_qa_numbers",
    "extract_models",
    "extract_dates",
]
