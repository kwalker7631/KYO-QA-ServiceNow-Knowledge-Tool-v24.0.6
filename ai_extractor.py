"""Thin wrapper around the optional ``extract`` package.

If the ``extract.ai_extractor`` module is unavailable, the exported
functions will raise a clear ``ImportError`` explaining how to install
the dependency or where to find the missing files.
"""

from __future__ import annotations

try:  # noqa: WPS501 - intentionally catching import error
    from extract.ai_extractor import QAExtractor
except ImportError:  # pragma: no cover - handled in tests
    QAExtractor = None  # type: ignore[assignment]

    def _missing(*_args, **_kwargs):  # noqa: D401 - simple helper
        """Raise a helpful error if the optional package isn't installed."""
        raise ImportError(
            "The optional 'extract' package is not installed. "
            "Add the 'extract' folder or install the package to use AI extraction."
        )

    ai_extract = _missing
    extract_qa_numbers = _missing
    extract_models = _missing
    extract_dates = _missing
else:  # pragma: no cover - basic import path
    _extractor = QAExtractor()
    ai_extract = _extractor.extract
    extract_qa_numbers = _extractor.extract_qa_numbers
    extract_models = _extractor.extract_models
    extract_dates = _extractor.extract_dates
