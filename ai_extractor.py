# KYO QA ServiceNow AI Extractor - SYNTAX FIXED VERSION
import re
from datetime import datetime
from logging_utils import setup_logger, log_info, log_error, log_warning, log_safe
from config import STANDARDIZATION_RULES
from ocr_utils import get_pdf_metadata
from data_harvesters import identify_document_type

logger = setup_logger("ai_extractor")

def ai_extract(text, pdf_path):
    """
    BULLETPROOF extraction function - guaranteed to work.
    """
    try:
        filename = pdf_path.name
        log_info(logger, f"Starting extraction for: {filename}")

        # Use bulletproof extraction
        data = bulletproof_extraction(text, filename)

        # Supplement with metadata
        metadata = get_pdf_metadata(pdf_path)
        if not data.get("author") or data["author"] == STANDARDIZATION_RULES["default_author"]:
            if metadata.get("author"):
                data["author"] = metadata["author"]
        
        # Identify document type
        data["document_type"] = identify_document_type(text)

        # Log the final result for debugging
        log_info(logger, f"FINAL EXTRACTION RESULT for {filename}:")
        log_safe(logger, f"  Full QA: '{data.get('full_qa_number', '')}'")
        log_safe(logger, f"  Short QA: '{data.get('short_qa_number', '')}'")
        log_safe(logger, f"  Models: '{data.get('models', '')}'")
        log_safe(logger, f"  Subject: '{data.get('subject', '')}'")
        log_safe(logger, f"  Date: '{data.get('published_date', '')}'")

        return data

    except Exception as e:
        log_error(logger, f"Critical error in ai_extract for {pdf_path.name}: {e}")
        return create_error_data(pdf_path.name)

def create_error_data(filename):
    """Create error data structure."""
    return {
        "full_qa_number": "", 
        "short_qa_number": "", 
        "models": "Extraction Error",
        "subject": f"Error processing {filename}",
        "author": STANDARDIZATION_RULES["default_author"], 
        "published_date": "",
        "document_type": "Unknown", 
        "needs_review": True
    }

def extract_qa_numbers(text, filename):
    """Return full and short QA numbers if found."""
    qa_extracted = False
    full_qa = short_qa = ""

    # Method 1: Ref. No. pattern (most common)
    if not qa_extracted:
        patterns = [
            r"Ref\.\s*No\.\s*([A-Z0-9]{2,4}[-]?\d{4})\s*\(([A-Z]\d{2,4})\)",
            r"Ref\s*No\s*[\.:]?\s*([A-Z0-9]{2,4}[-]?\d{4})\s*\(([A-Z]\d{2,4})\)",
            r"Reference\s*No\s*[\.:]?\s*([A-Z0-9]{2,4}[-]?\d{4})\s*\(([A-Z]\d{2,4})\)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                full_qa, short_qa = matches[0]
                full_qa, short_qa = full_qa.strip(), short_qa.strip()
                log_info(logger, f"Method 1 - Ref No found: {full_qa} ({short_qa})")
                qa_extracted = True
                break

    # Method 2: Service Bulletin pattern
    if not qa_extracted:
        patterns = [
            r"Service\s+Bulletin\s+([A-Z0-9]{2,4}[-]?\d{4})\s*\(([A-Z]\d{2,4})\)",
            r"([A-Z0-9]{2,4}[-]?\d{4})\s*\(([A-Z]\d{2,4})\)",  # Direct pattern
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                full_qa, short_qa = matches[0]
                full_qa, short_qa = full_qa.strip(), short_qa.strip()
                log_info(logger, f"Method 2 - Service Bulletin found: {full_qa} ({short_qa})")
                qa_extracted = True
                break

    # Method 3: Any format with parentheses
    if not qa_extracted:
        pattern = r"([A-Z]{2,4}[-]?\d{4})\s*\(([A-Z]\d{2,4})\)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            full_qa, short_qa = matches[0]
            full_qa, short_qa = full_qa.strip(), short_qa.strip()
            log_info(logger, f"Method 3 - General pattern found: {full_qa} ({short_qa})")
            qa_extracted = True

    # Method 4: Filename extraction
    if not qa_extracted:
        full_qa, short_qa = extract_from_filename_bulletproof(filename)
        if full_qa:
            log_info(logger, f"Method 4 - Filename extraction: {full_qa} ({short_qa})")
            qa_extracted = True

    if not qa_extracted:
        log_warning(logger, f"NO QA NUMBER FOUND for {filename}")

    return full_qa, short_qa


def extract_models(text, filename):
    """Return extracted model string."""
    models_extracted = False
    models = ""

    # Method 1: "Model:" line
    if not models_extracted:
        patterns = [
            r"Model\s*:\s*([^\n\r]+?)(?:\n|Classification:|Subject:|timing:|Phenomenon:|$)",
            r"Models\s*:\s*([^\n\r]+?)(?:\n|Classification:|Subject:|timing:|Phenomenon:|$)",
            r"Model\s+([^\n\r]+?)(?:\n|Classification:|Subject:|timing:|Phenomenon:|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                models = matches[0].strip()
                models = re.sub(r"\s+", " ", models)
                models = re.sub(r"\s*,\s*", ", ", models)
                if len(models) > 3 and not any(word in models.lower() for word in ["classification", "subject", "timing"]):
                    log_info(logger, f"Method 1 - Model line found: {models[:100]}...")
                    models_extracted = True
                    break

    # Method 2: Look for TASKalfa or ECOSYS patterns
    if not models_extracted:
        model_patterns = [
            r"((?:TASKalfa|ECOSYS)\s+[A-Za-z0-9\s,\-\(\)]+?)(?:\n\n|\s{3,}|Classification:|Subject:|$)",
            r"([A-Z]{2,}\s*[\w\-\s,]+?(?:ci|i|dn|cidn)\b(?:\s*,\s*[A-Z]{2,}\s*[\w\-\s]+?(?:ci|i|dn|cidn)\b)*)",
        ]

        for pattern in model_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                models = matches[0].strip()
                models = re.sub(r"\s+", " ", models)
                models = re.sub(r"\s*,\s*", ", ", models)
                if len(models) > 5:
                    log_info(logger, f"Method 2 - Pattern match found: {models[:100]}...")
                    models_extracted = True
                    break

    if not models_extracted:
        log_warning(logger, f"NO MODELS FOUND for {filename}")
        models = "Not Found"

    return models


def extract_dates(text, filename):
    """Return publication date in YYYY-MM-DD format if found."""
    date_patterns = [
        r"<Date>\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
        r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})",
        r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})",
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                match = matches[0]
                if isinstance(match[0], str) and match[0].isalpha():
                    date_str = f"{match[0]} {match[1]} {match[2]}"
                    formatted_date = datetime.strptime(date_str, "%B %d %Y").strftime("%Y-%m-%d")
                else:
                    if len(match[0]) == 4:  # YYYY-MM-DD
                        formatted_date = f"{match[0]}-{match[1].zfill(2)}-{match[2].zfill(2)}"
                    else:  # MM/DD/YYYY or DD/MM/YYYY
                        formatted_date = f"{match[2]}-{match[0].zfill(2)}-{match[1].zfill(2)}"
                log_info(logger, f"Date found: {formatted_date}")
                return formatted_date
            except (ValueError, IndexError):
                continue

    log_warning(logger, f"NO DATE FOUND for {filename}")
    return ""


def bulletproof_extraction(text, filename):
    """
    BULLETPROOF extraction - tries every possible method.
    """
    data = {
        "full_qa_number": "",
        "short_qa_number": "",
        "models": "",
        "author": STANDARDIZATION_RULES.get("default_author", "Knowledge Import"),
        "published_date": "",
        "subject": "",
    }

    log_info(logger, f"Starting bulletproof extraction for: {filename}")
    log_info(logger, f"Text length: {len(text)} characters")
    
    # Only log the presence of text to avoid leaking PDF content
    if len(text) > 0:
        log_info(logger, f"Text available for {filename} ({len(text)} characters)")
    else:
        log_warning(logger, f"No text to process for {filename}")
        return data

    # ===== QA NUMBER EXTRACTION =====
    full_qa, short_qa = extract_qa_numbers(text, filename)
    data["full_qa_number"] = full_qa
    data["short_qa_number"] = short_qa

    # ===== MODEL EXTRACTION =====
    data["models"] = extract_models(text, filename)

    # ===== DATE EXTRACTION =====
    data["published_date"] = extract_dates(text, filename)

    # ===== SUBJECT EXTRACTION =====
    subject_extracted = False
    
    subject_patterns = [
        r"Subject\s*:\s*([^\n\r]+(?:\n[^\n\r]*?)*?)(?:Model:|Classification:|timing:|Phenomenon:|$)",
        r"Subject\s+([^\n\r]+(?:\n[^\n\r]*?)*?)(?:Model:|Classification:|timing:|Phenomenon:|$)",
        r"Title\s*:\s*([^\n\r]+)",
    ]

    for pattern in subject_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            subject = matches[0].strip()
            # Clean up subject
            subject = re.sub(r'\s+', ' ', subject)
            subject = subject.replace('\n', ' ').strip()
            
            if len(subject) > 5:
                data["subject"] = subject
                log_safe(logger, f"Subject found: {data['subject'][:100]}...")
                subject_extracted = True
                break

    # Fallback subject from filename
    if not subject_extracted:
        clean_subject = filename.replace('_', ' ').replace('.pdf', '')
        clean_subject = re.sub(r'QA_[A-Z0-9]+_', '', clean_subject)
        clean_subject = re.sub(r'_SB.*', '', clean_subject)
        data["subject"] = clean_subject.strip()
        log_safe(logger, f"Using filename as subject: {data['subject']}")

    return data

def extract_from_filename_bulletproof(filename):
    """Extract QA numbers from filename - multiple patterns."""
    try:
        log_info(logger, f"Trying filename extraction on: {filename}")
        
        # Pattern 1: QA_M105_2XD_0052_SB_rev.1.pdf
        match = re.search(r'QA_([A-Z]\d{2,4})_([A-Z0-9]{2,4})[-_](\d{4})', filename)
        if match:
            short_qa = match.group(1)  # M105
            full_qa = f"{match.group(2)}-{match.group(3)}"  # 2XD-0052
            log_info(logger, f"Filename pattern 1 matched: {full_qa} ({short_qa})")
            return full_qa, short_qa
        
        # Pattern 2: QA_20146_E014-2LV-0032r2.pdf  
        match = re.search(r'QA_\d+_([A-Z]\d{2,4})[-_]([A-Z0-9]{2,4})[-_](\d{4})', filename)
        if match:
            short_qa = match.group(1)  # E014
            full_qa = f"{match.group(2)}-{match.group(3)}"  # 2LV-0032
            log_info(logger, f"Filename pattern 2 matched: {full_qa} ({short_qa})")
            return full_qa, short_qa
        
        # Pattern 3: QA_P058_2XD-0116_SB.pdf
        match = re.search(r'QA_([A-Z]\d{2,4})_([A-Z0-9]{2,4})[-_](\d{4})', filename)
        if match:
            short_qa = match.group(1)  # P058
            full_qa = f"{match.group(2)}-{match.group(3)}"  # 2XD-0116
            log_info(logger, f"Filename pattern 3 matched: {full_qa} ({short_qa})")
            return full_qa, short_qa
        
        # Pattern 4: Any QA_XXX_YYY pattern
        match = re.search(r'QA_([A-Z]\d{2,4})_([A-Z0-9]{2,4}[-_]\d{4})', filename)
        if match:
            short_qa = match.group(1)
            full_qa = match.group(2).replace('_', '-')
            log_info(logger, f"Filename pattern 4 matched: {full_qa} ({short_qa})")
            return full_qa, short_qa
            
        log_warning(logger, f"No filename patterns matched for: {filename}")
        
    except Exception as e:
        log_error(logger, f"Filename extraction error: {e}")
    
    return "", ""