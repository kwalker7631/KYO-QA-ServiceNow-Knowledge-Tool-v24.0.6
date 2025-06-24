import openpyxl
from pathlib import Path
from excel_generator import generate_excel


def test_generate_excel_no_template(tmp_path):
    data = [{"A": 1, "B": "two"}]
    out_file = tmp_path / "result.xlsx"
    returned = generate_excel(data, out_file, None)
    assert Path(returned).exists()
    wb = openpyxl.load_workbook(out_file)
    sheet = wb.active
    headers = [cell.value for cell in sheet[1]]
    assert headers == ["A", "B"]


def test_generate_excel_no_template_returns_path(tmp_path):
    data = [{"A": "first", "B": "second"}]
    out_file = tmp_path / "out.xlsx"
    returned = generate_excel(data, out_file, None)
    assert returned == str(out_file)
    wb = openpyxl.load_workbook(out_file)
    sheet = wb.active
    assert sheet["A2"].alignment.wrap_text


def test_column_width_expands_with_long_value(tmp_path):
    long_text = "A" * 40
    data = [{"A": long_text}]
    out_file = tmp_path / "long.xlsx"
    generate_excel(data, out_file, None)
    wb = openpyxl.load_workbook(out_file)
    sheet = wb.active
    width = sheet.column_dimensions["A"].width
    assert width and width > 20
