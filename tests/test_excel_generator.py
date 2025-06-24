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

def test_apply_formatting_wrap_and_fill(tmp_path):
    from openpyxl import Workbook
    from excel_generator import _apply_formatting, REVIEW_FILL

    wb = Workbook()
    sheet = wb.active
    sheet.append(["col1", "needs_review", "col3"])
    sheet.append(["a", "TRUE", "c"])
    sheet.append(["d", "", "f"])

    _apply_formatting(sheet)

    # Row with needs_review TRUE should have fill applied
    for cell in sheet[2]:
        assert cell.alignment.wrap_text
        assert cell.fill.start_color.rgb == REVIEW_FILL.start_color.rgb
    # Row without needs_review should not be filled
    for cell in sheet[3]:
        assert cell.alignment.wrap_text
        assert cell.fill.start_color.rgb != REVIEW_FILL.start_color.rgb
