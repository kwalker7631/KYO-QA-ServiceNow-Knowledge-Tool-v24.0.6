# KYO QA ServiceNow Excel Generator v24.0.6
import pandas as pd, shutil, openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, PatternFill
from openpyxl.formatting.rule import FormulaRule
from logging_utils import setup_logger, log_info, log_error, log_warning
from custom_exceptions import ExcelGenerationError

logger = setup_logger("excel_generator")

# Default cell styling
REVIEW_FILL = PatternFill(start_color="FFF3BF", end_color="FFF3BF", fill_type="solid")

def _apply_formatting(sheet: openpyxl.worksheet.worksheet.Worksheet):
    """Apply default formatting to the given worksheet."""
    review_idx = None
    status_idx = None
    for idx, cell in enumerate(sheet[1], start=1):
        header = str(cell.value).lower()
        if header == "needs_review":
            review_idx = idx
        if header == "status":
            status_idx = idx

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True)

        if review_idx and str(row[review_idx - 1].value).lower() in {"true", "needs_review", "1"}:
            for cell in row:
                cell.fill = REVIEW_FILL

    for column in sheet.columns:
        max_len = max(len(str(c.value)) if c.value is not None else 0 for c in column)
        sheet.column_dimensions[column[0].column_letter].width = max(max_len + 2, 15)

    if status_idx:
        status_letter = get_column_letter(status_idx)
        last_letter = get_column_letter(sheet.max_column)
        data_range = f"A2:{last_letter}{sheet.max_row}"
        formula = (
            f'OR(${status_letter}2="needs_review",'
            f'${status_letter}2="failed",'
            f'${status_letter}2="needs_ocr")'
        )
        sheet.conditional_formatting.add(
            data_range,
            FormulaRule(formula=[formula], fill=REVIEW_FILL)
        )

def _use_template_excel(df, output_path, template_path):
    """Write DataFrame to an Excel file based on an existing template."""
    try:
        shutil.copy2(template_path, output_path)
        workbook = openpyxl.load_workbook(output_path)
        sheet = workbook["Page 1"] if "Page 1" in workbook.sheetnames else workbook.active
        for row in dataframe_to_rows(df, index=False, header=False):
            sheet.append(row)
        _apply_formatting(sheet)
        workbook.save(output_path)
        log_info(logger, f"Successfully saved data to {output_path}")
        return str(output_path)
    except Exception as e:
        raise ExcelGenerationError(f"Failed to write data to template: {e}")


def _create_new_excel(df, output_path):
    """Write DataFrame to a brand new Excel file when no template is provided."""
    try:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        for row in dataframe_to_rows(df, index=False, header=True):
            sheet.append(row)
        _apply_formatting(sheet)
        workbook.save(output_path)
        log_info(logger, f"Successfully saved data to {output_path}")
        return str(output_path)
    except Exception as e:
        raise ExcelGenerationError(f"Failed to write data: {e}")

def generate_excel(all_results, output_path, template_path):
    try:
        if not all_results: raise ExcelGenerationError("No data to generate.")
        df = pd.DataFrame(all_results)
        
        if template_path:
            log_info(logger, f"Aligning data with template: {template_path}")
            workbook = openpyxl.load_workbook(template_path)
            sheet = workbook["Page 1"] if "Page 1" in workbook.sheetnames else workbook.active
            template_headers = [cell.value for cell in sheet[1] if cell.value]
            workbook.close()
            if not template_headers:
                raise ExcelGenerationError("No headers in template.")

            extra_cols = [col for col in df.columns if col not in template_headers]
            if extra_cols:
                log_warning(logger, f"Dropping non-template columns: {extra_cols}")
                df = df.drop(columns=extra_cols, errors='ignore')

            missing_cols = [col for col in template_headers if col not in df.columns]
            if missing_cols:
                log_warning(logger, f"Adding missing template columns: {missing_cols}")
                for col in missing_cols:
                    df[col] = ""

            df = df[template_headers]
            return _use_template_excel(df, output_path, template_path)
        else:
            log_info(logger, "No template provided. Creating new workbook.")
            df.to_excel(output_path, index=False)
            workbook = openpyxl.load_workbook(output_path)
            sheet = workbook.active
            _apply_formatting(sheet)
            workbook.save(output_path)
            log_info(logger, f"Successfully saved data to {output_path}")
            return str(output_path)
    except Exception as e:
        log_error(logger, f"Excel generation failed: {e}")
        raise ExcelGenerationError(f"Failed to generate Excel file: {e}")
