# KYO QA ServiceNow Processing Engine - FINAL VERSION
from version import VERSION
import os, re, zipfile
from pathlib import Path
import fitz
from datetime import datetime
from dateutil.relativedelta import relativedelta

from logging_utils import setup_logger, log_info, log_error, log_warning
from custom_exceptions import *
from file_utils import get_temp_dir, cleanup_temp_files, is_pdf, is_zip, save_txt, is_file_locked
from ocr_utils import extract_text_from_pdf
from ai_extractor import ai_extract
from excel_generator import generate_excel
from config import STANDARDIZATION_RULES

logger = setup_logger("processing_engine")

def parse_pdf_date(date_str):
    if not isinstance(date_str, str): return ""
    match = re.search(r"D:(\d{4})(\d{2})(\d{2})", date_str)
    if match:
        year, month, day = match.groups()
        try: return datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")
        except ValueError: return ""
    return date_str

def _is_ocr_needed(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            if not doc.is_pdf or doc.is_encrypted: return False
            return len("".join(page.get_text() for page in doc).strip()) < 100
    except Exception as e: return True

def process_single_pdf(pdf_path, txt_output_dir, progress_cb, ocr_cb, cancel_event):
    if cancel_event.is_set(): return None
    filename = Path(pdf_path).name
    log_info(logger, f"Processing PDF: {filename}")
    ocr_was_used = _is_ocr_needed(pdf_path)
    if ocr_was_used: ocr_cb(True)
    extracted_text = extract_text_from_pdf(pdf_path)
    ocr_cb(False)
    if not extracted_text: return create_error_record(filename, "TEXT EXTRACTION FAILED")
    save_txt(extracted_text, txt_output_dir / f"{Path(filename).stem}.txt")
    progress_cb(f"Analyzing content of {filename}...")
    extracted_data = ai_extract(extracted_text, Path(pdf_path))
    if ocr_was_used: extracted_data['processing_status'] = 'OCR Required'
    return map_to_servicenow_format(extracted_data, filename)

def process_files(folder, excel_path, template_path, progress_cb, ocr_cb, cancel_event):
    if is_file_locked(Path(excel_path)): raise FileLockError(f"File is locked: {excel_path}")
    source_folder, temp_dir, txt_output_dir = Path(folder), get_temp_dir(), Path.cwd() / "PDF_TXT"
    txt_output_dir.mkdir(exist_ok=True)
    files_to_process = [f for f in source_folder.iterdir() if is_pdf(f) or is_zip(f)]
    all_results = _process_file_list(files_to_process, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event)
    cleanup_temp_files(temp_dir)
    failed_count = sum(1 for r in all_results if "Extraction Error" in r.get("models", ""))
    if all_results and not cancel_event.is_set():
        final_excel_path = generate_excel(all_results, excel_path, template_path)
        review_list = [r for r in all_results if r.get("needs_review")]
        return final_excel_path, review_list, failed_count
    return None, [], 0

def process_pdf_list(pdf_paths, excel_path, template_path, progress_cb, ocr_cb, cancel_event):
    if is_file_locked(Path(excel_path)): raise FileLockError(f"File is locked: {excel_path}")
    temp_dir, txt_output_dir = get_temp_dir(), Path.cwd() / "PDF_TXT"
    txt_output_dir.mkdir(exist_ok=True)
    files_to_process = [Path(p) for p in pdf_paths]
    all_results = _process_file_list(files_to_process, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event)
    failed_count = sum(1 for r in all_results if "Extraction Error" in r.get("models", ""))
    if all_results and not cancel_event.is_set():
        final_excel_path = generate_excel(all_results, excel_path, template_path)
        review_list = [r for r in all_results if r.get("needs_review")]
        return final_excel_path, review_list, failed_count
    return None, [], 0

def _process_file_list(file_list, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event):
    all_results = []
    for i, file_path in enumerate(file_list):
        if cancel_event.is_set(): break
        progress_cb(f"Processing file {i+1}/{len(file_list)}: {file_path.name}")
        try:
            if is_pdf(file_path):
                result = process_single_pdf(file_path, txt_output_dir, progress_cb, ocr_cb, cancel_event)
                if result: all_results.append(result)
            elif is_zip(file_path):
                # This part was missing in some previous snippets, ensuring it's here
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    pdf_files = [f for f in zip_ref.namelist() if is_pdf(f) and not f.startswith('__MACOSX')]
                    extraction_path = temp_dir / file_path.stem
                    zip_ref.extractall(extraction_path)
                    for pdf_file in pdf_files:
                        if cancel_event.is_set(): break
                        result = process_single_pdf(extraction_path / pdf_file, txt_output_dir, progress_cb, ocr_cb, cancel_event)
                        if result: all_results.append(result)
        except Exception as e:
            log_error(logger, f"Critical error processing file {file_path.name}: {e}")
            all_results.append(create_error_record(file_path.name, "CRITICAL ERROR"))
    return all_results

def create_error_record(filename, error_msg):
    return map_to_servicenow_format({"models": "Extraction Error", "subject": f"ERROR: {error_msg}", "processing_status": "Failed"}, filename)

def map_to_servicenow_format(extracted_data, filename):
    # This line defines `needs_review` and fixes the NameError
    needs_review = not all(extracted_data.get(key) for key in ["full_qa_number", "models", "subject"]) or extracted_data.get('models') == 'Not Found'
    
    if 'processing_status' not in extracted_data:
        processing_status = 'Needs Review' if needs_review else 'Success'
    else:
        processing_status = extracted_data.get('processing_status')

    if needs_review and processing_status not in ['Failed', 'OCR Required']:
        log_warning(logger, f"Flagging '{filename}' for review.")
    
    qa_str, short_qa = extracted_data.get("full_qa_number", ""), extracted_data.get("short_qa_number", "")
    pub_date_val = parse_pdf_date(extracted_data.get("published_date", ""))
    date_str, formatted_date = "", ""
    if pub_date_val:
        try:
            dt_obj = datetime.strptime(pub_date_val, '%Y-%m-%d')
            date_str = f"<{pub_date_val}>"
            formatted_date = dt_obj.strftime('%-m/%-d/%Y')
        except (ValueError, TypeError): date_str = f"<{pub_date_val}>" if pub_date_val else ""
    subject = extracted_data.get("subject", "No Subject Found")
    short_description = f"{qa_str}, {date_str}, {subject}"
    valid_to_date = (datetime.now() + relativedelta(years=10)).strftime("%Y-%m-%d")
    models_data, meta_desc = extracted_data.get("models", ""), short_qa if short_qa else "QA"
    change_type = extracted_data.get("change_type", "N/A")
    return {
        "Active": "TRUE", "Article type": "HTML", "Author": extracted_data.get("author", STANDARDIZATION_RULES["default_author"]),
        "Category(category)": "Dealer", "Configuration item": "", "Confidence": "Validated", "Description": filename,
        "Attachment link": "", "Disable commenting": "FALSE", "Disable suggesting": "FALSE", "Display attachments": "FALSE",
        "Flagged": "FALSE", "Governance": "Compliance Based", "Category(kb_category)": "General Info", "Knowledge base": "Tech QA",
        "Meta": models_data, "Meta Description": meta_desc, "Ownership Group": "", "Published": formatted_date,
        "Scheduled publish date": "", "Short description": short_description, "Article body": "", "Topic": "General",
        "Problem Code": "", "models": models_data, "Ticket#": "", "Valid to": valid_to_date, "View as allowed": "TRUE",
        "Wiki": "", "Sys ID": "", "file_name": filename, "needs_review": needs_review, "Change Type": change_type,
        "processing_status": processing_status
    }