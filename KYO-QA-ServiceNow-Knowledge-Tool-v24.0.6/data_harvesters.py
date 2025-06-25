# KYO QA ServiceNow AI Extractor - FINAL INTELLIGENT VERSION
from version import VERSION
import re
from logging_utils import setup_logger, log_info, log_error, log_warning
from config import STANDARDIZATION_RULES, QA_NUMBER_PATTERNS, SHORT_QA_PATTERN, MODEL_PATTERNS

logger = setup_logger("ai_extractor")

def clean_text_for_extraction(text):
    """Removes repeating page headers/footers to reduce noise and improve accuracy."""
    text = re.sub(r'\(Page\.\d+/\d+\)', '', text)
    text = re.sub(r'Service\s+Bulletin\s+Ref\.', 'Ref.', text, flags=re.IGNORECASE)
    text = re.sub(r'For\s+authorized\s+KYOCERA\s+engineers\s+only\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Do\s+not\s+distribute\s+to\s+non-authorized\s+parties\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'CONFIDENTIAL', '', text, flags=re.IGNORECASE)
    text = re.sub(r'KYOCERA\s+Document\s+Solutions\s+Inc\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'A\s+B\s+C', '', text)
    text = re.sub(r'[\t ]+', ' ', text)
    return text

def ai_extract(text, pdf_path):
    """Intelligent extraction function that cleans text and uses multi-stage logic."""
    from data_harvesters import harvest_metadata, harvest_subject, identify_document_type
    
    try:
        filename = pdf_path.name
        log_info(logger, f"Starting intelligent extraction for: {filename}")
        
        cleaned_text = clean_text_for_extraction(text)
        # Pass both text and filename to the extractor
        data = bulletproof_extraction(cleaned_text, filename)

        supplemental_data = harvest_metadata(cleaned_text, pdf_path)
        data['published_date'] = data.get('published_date') or supplemental_data.get('published_date', '')
        data['author'] = data.get('author') or supplemental_data.get('author', STANDARDIZATION_RULES["default_author"])

        data["subject"] = harvest_subject(cleaned_text)
        data["document_type"] = identify_document_type(cleaned_text)

        if data.get('models') and data['models'] != "Not Found":
            data['Meta'] = ", ".join([m.strip() for m in data['models'].split(',')])

        log_info(logger, f"Final Data for {filename}: QA='{data.get('full_qa_number')}', Short QA='{data.get('short_qa_number')}', Models='{data.get('models', '')[:70]}...'")
        return data

    except Exception as e:
        log_error(logger, f"Critical error in ai_extract for {pdf_path.name}: {e}")
        return create_error_data(pdf_path.name)

def create_error_data(filename):
    """Creates a standardized record for processing errors."""
    return {
        "full_qa_number": "", "short_qa_number": "", "models": "Extraction Error",
        "subject": f"Error processing {filename}",
        "author": STANDARDIZATION_RULES.get("default_author", "System"), "published_date": "",
        "document_type": "Unknown", "needs_review": True, "Meta": ""
    }

def bulletproof_extraction(text, filename):
    """Core extraction function using multi-stage logic for high accuracy."""
    data = {"full_qa_number": None, "short_qa_number": None}

    # --- FIXED: Stage 1 - QA NUMBER EXTRACTION from both text and filename ---
    search_targets = [text, filename]
    
    for target in search_targets:
        if data.get('full_qa_number'): break # Stop if we found it in the text
        
        for pattern in QA_NUMBER_PATTERNS:
            match = re.search(pattern, target, re.IGNORECASE)
            if match:
                # Handle the new E-number pattern with two groups
                if pattern == r"\b(E\d+)-([A-Z0-9]{2,}[-][0-9A-Z]+)\b":# KYO QA ServiceNow Data Harvesters - FINAL VERSION
from version import VERSION
import re
from logging_utils import setup_logger, log_info, log_error, log_warning
from config import DATE_PATTERNS, SUBJECT_PATTERNS, STANDARDIZATION_RULES, APP_SOFTWARE_PATTERNS

logger = setup_logger("data_harvesters")

def harvest_subject(text, qa_number=None):
    """Extracts a clean subject, removing the QA number if present."""
    subject = "No subject found"
    for pattern in SUBJECT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            subject = match.group(1).strip()
            subject = re.sub(r'\s+', ' ', subject)
            if qa_number and qa_number in subject:
                subject = subject.replace(qa_number, "").strip(" -")
            max_len = STANDARDIZATION_RULES.get("max_subject_length", 250)
            if len(subject) > max_len:
                subject = subject[:max_len].rsplit(' ', 1)[0] + '...'
            break
    return subject

def harvest_metadata(text, pdf_path=None):
    """Extracts supplemental metadata like dates and authors."""
    from ocr_utils import get_pdf_metadata
    pdf_metadata = get_pdf_metadata(pdf_path) if pdf_path else {}
    results = {"published_date": "", "author": STANDARDIZATION_RULES["default_author"]}
    for pattern in DATE_PATTERNS:
        pub_regex = rf"(?:published|issue(?:d)?|publication|revision\s*date)[^\n:]*[:\s]*({pattern})"
        pub_match = re.search(pub_regex, text, re.IGNORECASE)
        if pub_match:
            results['published_date'] = pub_match.group(1)
            break
    if not results.get('published_date'):
         for key in ("modDate", "creationDate"):
            if pdf_metadata.get(key):
                results['published_date'] = pdf_metadata[key]
                break
    author_match = re.search(r'\b(?:author|created\s+by):?\s*([A-Za-z\s]+)(?:\n|$)', text, re.IGNORECASE)
    if author_match:
         results['author'] = author_match.group(1).strip()
    elif pdf_metadata.get("author"):
        results['author'] = pdf_metadata["author"]
    return results

def identify_document_type(text):
    """Identifies the document type from its content."""
    text_lower = text.lower()
    if re.search(r'\bservice\s+bulletin\b', text_lower): return "Service Bulletin"
    if re.search(r'\b(?:qa|quality\s+assurance)\b', text_lower): return "Quality Assurance"
    if re.search(r'\btechnical\s+(?:bulletin|note)\b', text_lower): return "Technical Bulletin"
    if re.search(APP_SOFTWARE_PATTERNS["keywords"], text_lower, re.IGNORECASE): return "Software Bulletin"
    return "Unknown"
                    data['short_qa_number'] = match.group(1).strip()
                    data['full_qa_number'] = match.group(2).strip()
                    log_info(logger, f"QA Number extracted from '{target[:30]}...' using E-number pattern.")
                    break
                # Handle patterns with the (Pxxx) short code
                elif len(match.groups()) > 1 and match.group(2):
                    data['full_qa_number'] = match.group(1).strip()
                    data['short_qa_number'] = match.group(2).strip()
                    log_info(logger, f"QA Number extracted from '{target[:30]}...' using P-number pattern.")
                    break
                # Handle patterns with only a full QA number
                else:
                    data['full_qa_number'] = match.group(1).strip()
                    # Try to find a short code separately
                    short_match = re.search(SHORT_QA_PATTERN, target, re.IGNORECASE)
                    if short_match:
                        data['short_qa_number'] = short_match.group(1)
                    log_info(logger, f"QA Number extracted from '{target[:30]}...' using general pattern.")
                    break
        if data.get('full_qa_number'): break

    # Stage 2: MODEL EXTRACTION
    for pattern in MODEL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            models_text = re.sub(r'\s+', ' ', match.group(1)).strip(' ,-')
            data['models'] = models_text
            log_info(logger, f"Extracted models: {models_text[:100]}...")
            break

    if not data.get('models'):
        data['models'] = "Not Found"
        
    return data
