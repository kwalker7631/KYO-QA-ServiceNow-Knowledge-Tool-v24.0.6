import sys
from pathlib import Path
import pandas as pd
import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from excel_generator import _use_template_excel  # noqa: E402


def create_template(tmp_dir: Path) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Page 1"
    ws.append(["text", "status"])
    path = tmp_dir / "template.xlsx"
    wb.save(path)
    wb.close()
    return path


def test_status_row_coloring(tmp_path: Path):
    df = pd.DataFrame([
        {"text": "hello", "status": "needs_review"},
        {"text": "world", "status": "ok"},
        {"text": "foo", "status": "failed"},
    ])
    template = create_template(tmp_path)
    output = tmp_path / "out.xlsx"

    _use_template_excel(df, output, template)

    wb = openpyxl.load_workbook(output)
    ws = wb["Page 1"]

    assert ws["A2"].fill.fill_type == "solid"
    assert ws["A3"].fill.fill_type in (None, "none")
    assert ws["A4"].fill.fill_type == "solid"
    assert ws["A2"].alignment.wrap_text
    assert ws.column_dimensions["A"].width > 0
    wb.close()
