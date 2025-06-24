import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import types
sys.modules.setdefault('fitz', types.SimpleNamespace(open=lambda *a, **k: None))
import pytest
try:
    import pandas
    import openpyxl
except ImportError:
    pytest.skip("pandas/openpyxl missing", allow_module_level=True)
from kyoqa.processing_engine import map_to_servicenow_format


def test_map_to_servicenow_flags_missing_fields():
    data = {
        "full_qa_number": "2M8-0016",
        "short_qa_number": "E099",
        "models": "",
        "subject": "",
        "published_date": "2024-01-15",
        "author": "Author",
        "document_type": "Service Bulletin",
    }

    record = map_to_servicenow_format(data, "test.pdf")

    assert record["needs_review"] is True
