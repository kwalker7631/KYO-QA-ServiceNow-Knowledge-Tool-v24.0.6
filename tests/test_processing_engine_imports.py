import importlib
import os
import sys
import types
import pytest

# Ensure the project root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.modules.setdefault('fitz', types.SimpleNamespace(open=lambda *a, **k: None))
try:
    import pandas
    import openpyxl
except ImportError:
    pytest.skip("pandas/openpyxl missing", allow_module_level=True)

import kyoqa.custom_exceptions as custom_exceptions

# Ensure processing_engine exposes same exception classes
processing_engine = importlib.import_module('kyoqa.processing_engine')


def test_exception_exports():
    assert processing_engine.QAExtractionError is custom_exceptions.QAExtractionError
    assert processing_engine.FileProcessingError is custom_exceptions.FileProcessingError
    assert processing_engine.ExcelGenerationError is custom_exceptions.ExcelGenerationError
    assert processing_engine.OCRError is custom_exceptions.OCRError
    assert processing_engine.ZipExtractionError is custom_exceptions.ZipExtractionError
    assert processing_engine.ConfigurationError is custom_exceptions.ConfigurationError
