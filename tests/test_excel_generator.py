import sys
from pathlib import Path
import pytest
sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    import pandas
    import openpyxl
except ImportError:
    pytest.skip("pandas/openpyxl missing", allow_module_level=True)

from kyoqa.excel_generator import generate_excel


def test_generate_excel_writes_rows(tmp_path):
    if openpyxl is None:
        pytest.skip("openpyxl not installed")
    headers = ["Active", "Article type", "Author"]
    template = tmp_path / "template.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Page 1"
    ws.append(headers)
    wb.save(template)

    data = [{"Active": "TRUE", "Article type": "HTML", "Author": "Tester"}]
    output = tmp_path / "out.xlsx"
    generate_excel(data, output, template)

    result_wb = openpyxl.load_workbook(output)
    result_ws = result_wb["Page 1"]

    assert result_ws.max_row == 2
    assert [cell.value for cell in result_ws[2]] == ["TRUE", "HTML", "Tester"]
