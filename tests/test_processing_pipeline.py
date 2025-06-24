from unittest.mock import patch
import threading
import types
import sys
import pytest
sys.modules.setdefault('fitz', types.SimpleNamespace(open=lambda *a, **k: None))
try:
    import pandas
    import openpyxl
except ImportError:
    pytest.skip("pandas/openpyxl missing", allow_module_level=True)
sys.modules.setdefault('pandas', types.ModuleType('pandas'))
sys.modules.setdefault('openpyxl', types.ModuleType('openpyxl'))
from kyoqa import processing_engine


def test_process_pdf_list_returns_excel(tmp_path):
    dummy_pdf = tmp_path / "file.pdf"
    dummy_pdf.write_text("dummy")
    excel_out = tmp_path / "out.xlsx"
    template = tmp_path / "template.xlsx"

    with patch("kyoqa.processing_engine._process_file_list") as mock_proc, \
         patch("kyoqa.processing_engine.generate_excel") as mock_gen, \
         patch("kyoqa.processing_engine.get_temp_dir") as mock_temp:
        mock_proc.return_value = ([{"file_name": dummy_pdf.name}], [])
        mock_gen.return_value = str(excel_out)
        mock_temp.return_value = tmp_path

        def progress(_):
            pass

        def ocr(_):
            pass
        cancel_event = threading.Event()
        result = processing_engine.process_pdf_list(
            [dummy_pdf], excel_out, template, progress, ocr, cancel_event
        )

    final_path, review_list, fail_count = result
    assert final_path == str(excel_out)
    assert review_list == []
    assert fail_count == 0
