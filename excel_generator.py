# KYO QA ServiceNow Excel Generator v24.0.6
import pandas as pd
import shutil
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, PatternFill
from logging_utils import setup_logger, log_info, log_error, log_warning
from custom_exceptions import ExcelGenerationError

logger = setup_logger("excel_generator")


def _use_template_excel(df, output_path, template_path):
    try:
        shutil.copy2(template_path, output_path)
        workbook = openpyxl.load_workbook(output_path)
        sheet = (
            workbook["Page 1"]
            if "Page 1" in workbook.sheetnames
            else workbook.active
        )
        for row in dataframe_to_rows(df, index=False, header=False):
            sheet.append(row)

        alignment = Alignment(wrap_text=True)
        for col in sheet.iter_cols(min_row=1, max_row=sheet.max_row):
            max_len = max(
                len(str(c.value)) if c.value is not None else 0
                for c in col
            )
            sheet.column_dimensions[col[0].column_letter].width = max_len + 2
            for cell in col:
                cell.alignment = alignment

        status_map = {
            "needs_review": PatternFill(
                start_color="FFFFF599",
                end_color="FFFFF599",
                fill_type="solid",
            ),
            "failed": PatternFill(
                start_color="FFFFC7CE",
                end_color="FFFFC7CE",
                fill_type="solid",
            ),
            "needs_ocr": PatternFill(
                start_color="FFB8CCE4",
                end_color="FFB8CCE4",
                fill_type="solid",
            ),
        }
        status_col = None
        for idx, cell in enumerate(sheet[1], 1):
            if str(cell.value).lower() == "status":
                status_col = idx
                break
        if status_col:
            for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
                status_val = str(row[status_col - 1].value).lower()
                fill = status_map.get(status_val)
                if fill:
                    for c in row:
                        c.fill = fill

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
            log_info(
                logger,
                f"Aligning data with template: {template_path}",
            )
            workbook = openpyxl.load_workbook(template_path)
            sheet = (
                workbook["Page 1"]
                if "Page 1" in workbook.sheetnames
                else workbook.active
            )
            template_headers = [cell.value for cell in sheet[1] if cell.value]
            workbook.close()
            if not template_headers:
                raise ExcelGenerationError("No headers in template.")

            extra_cols = [
                col for col in df.columns
                if col not in template_headers
            ]
            if extra_cols:
                log_warning(
                    logger,
                    f"Dropping non-template columns: {extra_cols}",
                )
                df = df.drop(columns=extra_cols, errors='ignore')

            missing_cols = [
                col for col in template_headers
                if col not in df.columns
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
