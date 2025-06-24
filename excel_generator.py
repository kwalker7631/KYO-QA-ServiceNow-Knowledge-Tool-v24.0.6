# KYO QA ServiceNow Excel Generator v24.0.6
import pandas as pd, shutil, openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, PatternFill
from logging_utils import setup_logger, log_info, log_error, log_warning
from custom_exceptions import ExcelGenerationError

logger = setup_logger("excel_generator")

def _use_template_excel(df, output_path, template_path, highlight_map=None):
    """Write the DataFrame to the Excel template and apply formatting."""
    try:
        shutil.copy2(template_path, output_path)
        workbook = openpyxl.load_workbook(output_path)
        sheet = workbook["Page 1"] if "Page 1" in workbook.sheetnames else workbook.active

        start_row = sheet.max_row + 1
        for idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), start=start_row):
            sheet.append(row)
            for cell in sheet[idx]:
                cell.alignment = Alignment(wrap_text=True)

            if highlight_map:
                status = highlight_map.get(idx - start_row)
                if status:
                    fill_color = "FFEB9C" if status == "needs_review" else "FFC7CE"
                    fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                    for cell in sheet[idx]:
                        cell.fill = fill

        for column_cells in sheet.columns:
            length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = length + 2

        workbook.save(output_path)
        log_info(logger, f"Successfully saved data to {output_path}")
        return str(output_path)
    except Exception as e:
        raise ExcelGenerationError(f"Failed to write data to template: {e}")

def generate_excel(all_results, output_path, template_path):
    try:
        if not all_results: raise ExcelGenerationError("No data to generate.")
        df = pd.DataFrame(all_results)
        highlight_map = {}
        for idx, row in df.iterrows():
            if row.get("needs_review"):
                highlight_map[idx] = "needs_review"
            if str(row.get("status", "")).lower() == "failed":
                highlight_map[idx] = "failed"
        
        if template_path:
            log_info(logger, f"Aligning data with template: {template_path}")
            workbook = openpyxl.load_workbook(template_path)
            sheet = workbook["Page 1"] if "Page 1" in workbook.sheetnames else workbook.active
            template_headers = [cell.value for cell in sheet[1] if cell.value]
            workbook.close()
            if not template_headers: raise ExcelGenerationError("No headers in template.")

            extra_cols = [col for col in df.columns if col not in template_headers]
            if extra_cols:
                log_warning(logger, f"Dropping non-template columns: {extra_cols}")
                df = df.drop(columns=extra_cols, errors='ignore')

            missing_cols = [col for col in template_headers if col not in df.columns]
            if missing_cols:
                log_warning(logger, f"Adding missing template columns: {missing_cols}")
                for col in missing_cols: df[col] = ""
            
            df = df[template_headers]
        
        return _use_template_excel(df, output_path, template_path, highlight_map)
    except Exception as e:
        log_error(logger, f"Excel generation failed: {e}")
        raise ExcelGenerationError(f"Failed to generate Excel file: {e}")
