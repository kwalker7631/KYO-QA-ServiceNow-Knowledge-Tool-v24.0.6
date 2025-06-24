import openpyxl
from openpyxl.utils import get_column_letter
from excel_generator import generate_excel


def test_generate_excel_applies_styles(tmp_path):
    template = tmp_path / "template.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Page 1"
    ws.append(["col1", "status", "col3"])
    wb.save(template)

    output = tmp_path / "out.xlsx"
    data = [{"col1": "hello", "status": "needs_review", "col3": "x"}]
    generate_excel(data, output, template)

    wb2 = openpyxl.load_workbook(output)
    ws2 = wb2["Page 1"]

    assert ws2["A2"].alignment.wrap_text
    assert ws2.column_dimensions[get_column_letter(1)].width > len("col1")
    formulas = [
        rule.formula[0]
        for rules in ws2.conditional_formatting._cf_rules.values()
        for rule in rules
    ]
    assert '$B2="needs_review"' in formulas
