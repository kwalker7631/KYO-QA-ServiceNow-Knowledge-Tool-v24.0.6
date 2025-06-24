# KYO QA ServiceNow Processing Engine - FINALIZED MODEL MAPPING
import os
import re
import zipfile
from pathlib import Path
import fitz
from datetime import datetime, timedelta

from .logging_utils import setup_logger, log_info, log_error, log_warning
# Import custom exceptions explicitly so linters know where they come from
from .custom_exceptions import (
    QAExtractionError,
    FileProcessingError,
    ExcelGenerationError,
    OCRError,
    ZipExtractionError,
    ConfigurationError,
)
from .file_utils import get_temp_dir, cleanup_temp_files, is_pdf, is_zip, save_txt
from .ocr_utils import extract_text_from_pdf
from .ai_extractor import ai_extract
from .excel_generator import generate_excel
from .config import STANDARDIZATION_RULES

logger = setup_logger("processing_engine")

def _is_ocr_needed(pdf_path):
    """Checks if a PDF contains very little text, suggesting it's image-based and needs OCR."""
    try:
        with fitz.open(pdf_path) as doc:
            if not doc.is_pdf or doc.is_encrypted:
                return False
            text_content = "".join(page.get_text() for page in doc)
            return len(text_content.strip()) < 100
    except Exception as e:
        log_warning(logger, f"Could not pre-check PDF {pdf_path.name}: {e}")
        return True

def process_single_pdf(pdf_path, txt_output_dir, progress_cb, ocr_cb, cancel_event):
    """Processes a single PDF file and returns structured data."""
    if cancel_event.is_set(): 
        return None
        
    filename = Path(pdf_path).name
    log_info(logger, f"Processing PDF: {filename}")

    # Extract text
    if _is_ocr_needed(pdf_path):
        ocr_cb(True)
        log_info(logger, f"OCR required for {filename}.")
    
    extracted_text = extract_text_from_pdf(pdf_path)
    ocr_cb(False)
    
    if cancel_event.is_set(): 
        return None

    if not extracted_text:
        log_warning(logger, f"No text could be extracted from {filename}. Skipping.")
        return create_error_record(filename, "TEXT EXTRACTION FAILED")

    # Save extracted text for debugging
    txt_filename = txt_output_dir / f"{Path(filename).stem}.txt"
    save_txt(extracted_text, txt_filename)

    progress_cb(f"Analyzing content of {filename}...")

    # Extract data using AI extractor
    extracted_data = ai_extract(extracted_text, Path(pdf_path))
    
    # Log what we extracted for debugging
    log_info(logger, f"Raw extracted data for {filename}:")
    log_info(logger, f"  Full QA: '{extracted_data.get('full_qa_number', '')}'")
    log_info(logger, f"  Short QA: '{extracted_data.get('short_qa_number', '')}'") 
    log_info(logger, f"  Models: '{extracted_data.get('models', '')}'")
    log_info(logger, f"  Subject: '{extracted_data.get('subject', '')}'")

    # Validate and enhance the data
    validated_data = validate_and_enhance_data(extracted_data, filename)

    # Map to ServiceNow format
    servicenow_record = map_to_servicenow_format(validated_data, filename)

    return servicenow_record

def create_error_record(filename, error_msg):
    """Create a standardized error record."""
    return {
        "Active": "TRUE",
        "Article type": "HTML",
        "Author": STANDARDIZATION_RULES["default_author"],
        "Category(category)": "Dealer",
        "Configuration item": "",
        "Confidence": "Validated",
        "Description": filename,
        "Attachment link": "",
        "Disable commenting": "FALSE",
        "Disable suggesting": "FALSE", 
        "Display attachments": "FALSE",
        "Flagged": "FALSE",
        "Governance": "Compliance Based",
        "Category(kb_category)": "",
        "Knowledge base": "Tech QA",
        "Meta": "ERROR",
        "Meta Description": "ERROR", 
        "Ownership Group": "",
        "Published": "",
        "Scheduled publish date": "",
        "Short description": f"ERROR: {error_msg} - {filename}",
        "Article body": "",
        "Topic": "General",
        "Problem Code": "",
        "models": error_msg, 
        "Ticket#": "",
        "Valid to": "2036-03-04",
        "View as allowed": "TRUE",
        "Wiki": "",
        "Sys ID": "",
        # Internal tracking
        "file_name": filename,
        "needs_review": True
    }

def validate_and_enhance_data(extracted_data, filename):
    """Validate and enhance the extracted data."""
    
    # Ensure all required fields exist
    required_fields = ["full_qa_number", "short_qa_number", "models", "subject", "published_date", "author"]
    for field in required_fields:
        if field not in extracted_data:
            extracted_data[field] = ""
    
    # Clean up QA numbers
    if extracted_data["full_qa_number"]:
        qa_clean = extracted_data["full_qa_number"].strip()
        # Ensure proper format (e.g., 2ND-0148)
        if not re.match(r'^[A-Z0-9]{2,4}-\d{4}$', qa_clean):
            # Try to fix common issues
            qa_clean = re.sub(r'[^\w\-]', '', qa_clean)
            if '-' not in qa_clean and len(qa_clean) > 4:
                # Insert dash if missing (e.g., 2ND0148 -> 2ND-0148)
                qa_clean = qa_clean[:3] + '-' + qa_clean[3:]
        extracted_data["full_qa_number"] = qa_clean
    
    # Clean up short QA number
    if extracted_data["short_qa_number"]:
        short_clean = extracted_data["short_qa_number"].strip()
        short_clean = re.sub(r'[^\w]', '', short_clean)
        extracted_data["short_qa_number"] = short_clean
    
    # Validate date format
    if extracted_data["published_date"]:
        try:
            # Ensure YYYY-MM-DD format
            date_obj = datetime.strptime(extracted_data["published_date"], "%Y-%m-%d")
            extracted_data["published_date"] = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            log_warning(logger, f"Invalid date format: {extracted_data['published_date']}")
            extracted_data["published_date"] = ""
    
    # Clean up models
    if extracted_data["models"] and extracted_data["models"] != "Not Found":
        models_clean = extracted_data["models"].strip()
        # Remove excessive whitespace and clean up formatting
        models_clean = re.sub(r'\s+', ' ', models_clean)
        models_clean = re.sub(r'\s*,\s*', ', ', models_clean)
        # Remove any trailing punctuation
        models_clean = models_clean.rstrip('.,;')
        extracted_data["models"] = models_clean
        
        log_info(logger, f"Cleaned models for {filename}: '{models_clean}'")
    else:
        log_warning(logger, f"No models found for {filename}")
    
    # Clean up subject
    if extracted_data["subject"] and extracted_data["subject"] != "Not Found":
        subject_clean = extracted_data["subject"].strip()
        # Remove redundant information
        if extracted_data["full_qa_number"]:
            subject_clean = subject_clean.replace(extracted_data["full_qa_number"], "").strip()
        if extracted_data["short_qa_number"]:
            subject_clean = subject_clean.replace(f"({extracted_data['short_qa_number']})", "").strip()
        subject_clean = re.sub(r'\s+', ' ', subject_clean).strip(' ,-')
        extracted_data["subject"] = subject_clean
    
    return extracted_data

def map_to_servicenow_format(extracted_data, filename):
    """Map extracted data to ServiceNow import format - FIXED VERSION."""
    
    # Determine if this record needs review
    needs_review = False
    review_reasons = []
    
    if not extracted_data.get("full_qa_number"):
        needs_review = True
        review_reasons.append("Missing QA Number")
    
    if not extracted_data.get("models") or extracted_data["models"] in ["Not Found", ""]:
        needs_review = True
        review_reasons.append("Missing Models")
    
    if not extracted_data.get("subject") or extracted_data["subject"] in ["Not Found", ""]:
        needs_review = True
        review_reasons.append("Missing Subject")
    
    if needs_review:
        log_warning(logger, f"Flagging '{filename}' for review: {', '.join(review_reasons)}")
    
    # Build short description
    short_desc_parts = []
    
    if extracted_data.get("full_qa_number") and extracted_data.get("short_qa_number"):
        short_desc_parts.append(f"{extracted_data['full_qa_number']}({extracted_data['short_qa_number']})")
    
    if extracted_data.get("published_date"):
        try:
            pub_date_obj = datetime.strptime(extracted_data["published_date"], "%Y-%m-%d")
            short_desc_parts.append(f"<Date> {pub_date_obj.strftime('%B %d, %Y')}")
        except (ValueError, TypeError):
            if extracted_data["published_date"]:
                short_desc_parts.append(f"<Date> {extracted_data['published_date']}")
    
    if extracted_data.get("subject") and extracted_data["subject"] not in ["Not Found", ""]:
        short_desc_parts.append(extracted_data["subject"])
    
    short_description = " - ".join(short_desc_parts) if short_desc_parts else filename
    
    # Calculate valid to date (12 years from publish date)
    valid_to_date = "2036-03-04"  # Default fallback
    if extracted_data.get("published_date"):
        try:
            pub_date = datetime.strptime(extracted_data["published_date"], "%Y-%m-%d")
            valid_to_date = (pub_date + timedelta(days=12*365)).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    
    # Get models data for 'Meta' and 'models' fields
    models_data = ""
    if extracted_data.get("models") and extracted_data["models"] not in ["Not Found", ""]:
        models_data = extracted_data["models"]
        log_info(logger, f"Setting models data for {filename}: '{models_data}'")
    else:
        log_warning(logger, f"No models data to set for {filename}")
        
    # Build the 'Meta Description' field from the short QA number
    meta_description_data = "QA"
    if extracted_data.get("short_qa_number"):
        meta_description_data = f"QA, {extracted_data.get('short_qa_number')}"
    
    # Create the ServiceNow record with proper data types
    servicenow_record = {
        "Active": "TRUE",
        "Article type": extracted_data.get("document_type", "HTML"),
        "Author": extracted_data.get("author", STANDARDIZATION_RULES["default_author"]),
        "Category(category)": "Dealer", 
        "Configuration item": "",
        "Confidence": "Validated",
        "Description": filename,
        "Attachment link": "",
        "Disable commenting": "FALSE",
        "Disable suggesting": "FALSE",
        "Display attachments": "FALSE",
        "Flagged": "FALSE",
        "Governance": "Compliance Based",
        "Category(kb_category)": "",
        "Knowledge base": "Tech QA",
        "Meta": models_data if models_data else "QA",  # FINAL FIX: Models go here
        "Meta Description": meta_description_data, # FINAL FIX: "QA, E014" goes here
        "Ownership Group": "",
        "Published": extracted_data.get("published_date", ""),
        "Scheduled publish date": "",
        "Short description": short_description,
        "Article body": "",  # Keep empty as per template
        "Topic": "General",
        "Problem Code": "",
        "models": models_data, # Keep a dedicated 'models' field as well
        "Ticket#": "",
        "Valid to": valid_to_date,
        "View as allowed": "TRUE",
        "Wiki": "",
        "Sys ID": "",
        # Internal tracking fields (will be removed for final Excel)
        "file_name": filename,
        "needs_review": needs_review
    }
    
    # Log the final mapping for debugging
    log_info(logger, f"Final ServiceNow record for {filename}:")
    log_info(logger, f"  Meta: '{servicenow_record['Meta']}'") 
    log_info(logger, f"  Meta Description: '{servicenow_record['Meta Description']}'")
    log_info(logger, f"  models: '{servicenow_record['models']}'")
    log_info(logger, f"  Short description: '{servicenow_record['Short description'][:100]}...'")
    
    return servicenow_record

def process_zip_file(zip_path, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event):
    """Extracts all PDFs from a ZIP file and processes them individually."""
    if cancel_event.is_set(): 
        return []
        
    log_info(logger, f"Processing ZIP file: {zip_path.name}")
    results = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            pdf_files_in_zip = [f for f in zip_ref.namelist() 
                              if is_pdf(f) and not f.startswith('__MACOSX')]
            
            if not pdf_files_in_zip:
                log_warning(logger, f"No PDF files found in {zip_path.name}.")
                return []
            
            extraction_path = temp_dir / zip_path.stem
            zip_ref.extractall(extraction_path)
            
            for pdf_file in pdf_files_in_zip:
                if cancel_event.is_set(): 
                    break
                full_pdf_path = extraction_path / pdf_file
                result = process_single_pdf(full_pdf_path, txt_output_dir, progress_cb, ocr_cb, cancel_event)
                if result: 
                    results.append(result)
                    
        return results
        
    except zipfile.BadZipFile:
        log_error(logger, f"File is not a valid ZIP file: {zip_path.name}")
        return []
    except Exception as e:
        log_error(logger, f"Failed to process ZIP file {zip_path.name}: {e}")
        return []

def _process_file_list(file_list, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event):
    """Helper function to iterate through a list of files and process them."""
    all_results, failed_files = [], []
    total_files = len(file_list)

    for i, file_path in enumerate(file_list):
        if cancel_event.is_set():
            log_warning(logger, "Cancellation signal received. Stopping process.")
            break
        
        progress_cb(f"Processing file {i+1}/{total_files}: {file_path.name}")
        
        try:
            if is_pdf(file_path):
                result = process_single_pdf(file_path, txt_output_dir, progress_cb, ocr_cb, cancel_event)
                if result: 
                    all_results.append(result)
            elif is_zip(file_path):
                results = process_zip_file(file_path, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event)
                all_results.extend(results)
        except Exception as e:
            log_error(logger, f"Critical error processing file {file_path.name}: {e}")
            failed_files.append(file_path.name)

    return all_results, failed_files

def process_files(folder, excel_path, template_path, progress_cb, ocr_cb, cancel_event):
    """Main entry point to process all PDF and ZIP files in a given folder."""
    source_folder = Path(folder)
    temp_dir = get_temp_dir()
    txt_output_dir = Path.cwd() / "PDF_TXT"
    txt_output_dir.mkdir(exist_ok=True)
    
    files_to_process = [f for f in source_folder.iterdir() if is_pdf(f) or is_zip(f)]
    log_info(logger, f"Found {len(files_to_process)} files to process")

    all_results, failed_files = _process_file_list(files_to_process, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event)

    cleanup_temp_files(temp_dir)

    final_excel_path = None
    if all_results and not cancel_event.is_set():
        log_info(logger, f"Generating Excel file for {len(all_results)} processed documents.")
        final_excel_path = generate_excel(all_results, excel_path, template_path)
    else:
        log_warning(logger, "No data processed or process was cancelled. Excel file not generated.")

    review_list = [r["file_name"] for r in all_results if r.get("needs_review")]
    return final_excel_path, review_list, len(failed_files)

def process_pdf_list(pdf_paths, excel_path, template_path, progress_cb, ocr_cb, cancel_event):
    """Main entry point to process a specific list of PDF files."""
    temp_dir = get_temp_dir()
    txt_output_dir = Path.cwd() / "PDF_TXT"
    txt_output_dir.mkdir(exist_ok=True)
    
    files_to_process = [Path(p) for p in pdf_paths]
    log_info(logger, f"Processing {len(files_to_process)} individual files")

    all_results, failed_files = _process_file_list(files_to_process, temp_dir, txt_output_dir, progress_cb, ocr_cb, cancel_event)

    final_excel_path = None
    if all_results and not cancel_event.is_set():
        log_info(logger, f"Generating Excel file for {len(all_results)} processed documents.")
        final_excel_path = generate_excel(all_results, excel_path, template_path)
    else:
        log_warning(logger, "No data processed or process was cancelled. Excel file not generated.")

    review_list = [r["file_name"] for r in all_results if r.get("needs_review")]
    return final_excel_path, review_list, len(failed_files)
