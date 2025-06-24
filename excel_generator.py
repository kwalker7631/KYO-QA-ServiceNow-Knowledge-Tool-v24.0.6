# KYO QA ServiceNow Excel Generator v24.0.6
import pandas as pd
import shutil
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, PatternFill
from openpyxl.formatting.rule import FormulaRule
from logging_utils import setup_logger, log_info, log_error, log_warning
from custom_exceptions import ExcelGenerationError


logger = setup_logger("excel_generator")


def _use_template_excel(df, output_path, template_path):
    try:
        shutil.copy2(template_path, output_path)
        workbook = openpyxl.load_workbook(output_path)
        if "Page 1" in workbook.sheetnames:
            sheet = workbook["Page 1"]
        else:
            sheet = workbook.active
        for row in dataframe_to_rows(df, index=False, header=False):
            sheet.append(row)

        for col_idx, column_cells in enumerate(
            sheet.iter_cols(
                min_row=1,
                max_col=sheet.max_column,
                max_row=sheet.max_row,
            ),
            start=1,
        ):
            max_len = 0
            for cell in column_cells:
                if cell.value not in (None, ""):
                    cell.alignment = Alignment(wrap_text=True)
                    max_len = max(max_len, len(str(cell.value)))
            width = max_len + 2
            sheet.column_dimensions[get_column_letter(col_idx)].width = width

        if "status" in df.columns:
            status_index = df.columns.get_loc("status") + 1
            status_letter = get_column_letter(status_index)
            data_range = (
                f"A2:{get_column_letter(sheet.max_column)}{sheet.max_row}"
            )
            highlight_fill = PatternFill(
                start_color="FFF9CB5E",
                end_color="FFF9CB5E",
                fill_type="solid",
            )
            for val in ("needs_review", "failed", "needs_ocr"):
                formula = f"${status_letter}2=\"{val}\""
                rule = FormulaRule(
                    formula=[formula],
                    stopIfTrue=False,
                    fill=highlight_fill,
                )
                sheet.conditional_formatting.add(data_range, rule)

        workbook.save(output_path)
        log_info(logger, f"Successfully saved data to {output_path}")
        return str(output_path)
    except Exception as e:
        raise ExcelGenerationError(f"Failed to write data to template: {e}")


def generate_excel(all_results, output_path, template_path):
    try:
        if not all_results:
            raise ExcelGenerationError("No data to generate.")
        df = pd.DataFrame(all_results)

        if template_path:
            log_info(logger, f"Aligning data with template: {template_path}")
            workbook = openpyxl.load_workbook(template_path)
            if "Page 1" in workbook.sheetnames:
                sheet = workbook["Page 1"]
            else:
                sheet = workbook.active
            template_headers = [cell.value for cell in sheet[1] if cell.value]
            workbook.close()
            if not template_headers:
                raise ExcelGenerationError("No headers in template.")

            extra_cols = [
                col for col in df.columns if col not in template_headers
            ]
            if extra_cols:
                log_warning(
                    logger,
                    f"Dropping non-template columns: {extra_cols}",
                )
                df = df.drop(columns=extra_cols, errors="ignore")

            missing_cols = [
                col for col in template_headers if col not in df.columns
            ]
            if missing_cols:
                log_warning(
                    logger,
                    f"Adding missing template columns: {missing_cols}",
                )
                for col in missing_cols:
                    df[col] = ""

            df = df[template_headers]

        return _use_template_excel(df, output_path, template_path)
    except Exception as e:
        log_error(logger, f"Excel generation failed: {e}")
        raise ExcelGenerationError(f"Failed to generate Excel file: {e}")
