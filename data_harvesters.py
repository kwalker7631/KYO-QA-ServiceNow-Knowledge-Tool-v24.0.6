# KYO QA ServiceNow Data Harvesters
from version import VERSION
import re
from logging_utils import setup_logger, log_info, log_error, log_warning
from config import (
    DATE_PATTERNS,
    SUBJECT_PATTERNS,
    STANDARDIZATION_RULES,
    APP_SOFTWARE_PATTERNS,
)

logger = setup_logger("data_harvesters")

def harvest_subject(text):
    """Extract a subject or title for short_description."""
    try:
        if not text or len(text.strip()) < 10:
            log_warning(logger, "Input text too short for subject extraction")
            return "No subject found."

        # Clean text
        text = text.replace("\r", "\n").replace("\t", " ")
        text = re.sub(r'\s+', ' ', text)

        # Try subject patterns
        for pattern in SUBJECT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and len(match.group(1).strip()) > 10:
                subject = match.group(1).strip()
                max_length = STANDARDIZATION_RULES["max_subject_length"]
                if len(subject) > max_length:
                    subject = subject[:max_length-3] + "..."
                log_info(logger, f"Subject harvested: {subject[:60]}...")
                return subject

        # Fallback: AI-based summarization
        try:
            import ollama
            prompt = f"""
            Summarize the following text into a concise subject or title (10-100 characters).
            Avoid including model numbers or QA numbers.
            Text: {text[:2000]}
            """
            response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
            subject = response["message"]["content"].strip()
            if len(subject) > 10:
                max_length = STANDARDIZATION_RULES["max_subject_length"]
                subject = subject[:max_length-3] + "..." if len(subject) > max_length else subject
                log_info(logger, f"AI summarized subject: {subject[:60]}...")
                return subject
        except Exception as e:
            log_warning(logger, f"AI subject extraction failed: {e}. Using fallback.")

        # Fallback: First suitable paragraph
        paragraphs = [p.strip() for p in re.split(r'\n{2,}|\s{3,}', text) if p.strip()]
        for p in paragraphs:
            if 10 <= len(p) <= 500:
                max_length = STANDARDIZATION_RULES["max_subject_length"]
                subject = p[:max_length-3] + "..." if len(p) > max_length else p
                log_info(logger, f"Subject harvested (fallback): {subject[:60]}...")
                return subject

        log_warning(logger, "No suitable subject found.")
        return "No subject found."
    except Exception as e:
        log_error(logger, f"Subject harvest error: {e}")
        return "No subject found."

def harvest_metadata(text, pdf_path=None):
    """Extract comprehensive metadata from document text and PDF metadata."""
    try:
        from ocr_utils import get_pdf_metadata
        pdf_metadata = get_pdf_metadata(pdf_path) if pdf_path else {}
        results = {}

        # Extract date (prefer publication-like dates)
        for pattern in DATE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results['dates'] = list(set(matches))[:1]  # Take first date
                log_info(logger, f"Dates found: {results['dates']}")
                break
        if not results.get('dates') and pdf_metadata.get("creationDate"):
            results['dates'] = [pdf_metadata["creationDate"]]
            log_info(logger, f"Date from PDF metadata: {results['dates']}")

        # Extract published date
        for pattern in DATE_PATTERNS:
            pub_regex = rf"(?:published|issue(?:d)?|publication|revision\s*date)[^\n:]*[:\s]*({pattern})"
            pub_match = re.search(pub_regex, text, re.IGNORECASE)
            if pub_match:
                results['published_date'] = pub_match.group(1)
                log_info(logger, f"Published date found: {results['published_date']}")
                break
        if not results.get('published_date'):
            for key in ("modDate", "creationDate"):
                if pdf_metadata.get(key):
                    results['published_date'] = pdf_metadata[key]
                    log_info(logger, f"Published date from PDF metadata: {results['published_date']}")
                    break

        # Extract firmware version
        firmware_match = re.search(r'firmware\s+(?:version|upgrade)?[\s:]*([0-9.]+(?:\s*\w*)?)', text, re.IGNORECASE)
        if firmware_match:
            results['firmware'] = firmware_match.group(1).strip()
            log_info(logger, f"Firmware version found: {results['firmware']}")

        # Extract serial numbers (limit to 5)
        serial_matches = re.findall(r'\b[A-Z]{3}[0-9]{5,8}\b', text)
        if serial_matches:
            results['serial_numbers'] = list(set(serial_matches))[:5]
            log_info(logger, f"Serial numbers found: {', '.join(results['serial_numbers'])}")

        # Extract part numbers (limit to 5)
        part_matches = re.findall(r'\b[0-9]{2,3}[A-Z]{1,2}[0-9]{3,6}\b', text)
        if part_matches:
            results['part_numbers'] = list(set(part_matches))[:5]
            log_info(logger, f"Part numbers found: {', '.join(results['part_numbers'])}")

        # Extract author
        author_match = re.search(r'\b(?:author|created\s+by):?\s*([A-Za-z\s]+)(?:\n|$)', text, re.IGNORECASE)
        results['author'] = author_match.group(1).strip() if author_match else STANDARDIZATION_RULES["default_author"]
        if pdf_metadata.get("author"):
            results['author'] = pdf_metadata["author"]
        log_info(logger, f"Author: {results['author']}")

        return results
    except Exception as e:
        log_error(logger, f"Metadata harvest error: {e}")
        return {
            "dates": [STANDARDIZATION_RULES["default_date"]],
            "firmware": "", "serial_numbers": [], "part_numbers": [],
            "author": STANDARDIZATION_RULES["default_author"],
            "published_date": ""
        }

def identify_document_type(text):
    """Identify the type of document based on content."""
    try:
        text_lower = text.lower()
        if re.search(r'\bservice\s+bulletin\b', text_lower):
            return "Service Bulletin"
        elif re.search(r'\b(?:qa|quality\s+assurance)\b', text_lower):
            return "Quality Assurance"
        elif re.search(r'\btechnical\s+(?:bulletin|note)\b', text_lower):
            return "Technical Bulletin"
        elif re.search(r'\binstallation\s+(?:guide|manual|instruction)\b', text_lower):
            return "Installation Guide"
        elif re.search(r'\buser\s+(?:guide|manual)\b', text_lower):
            return "User Manual"
        elif re.search(r'\btroubleshooting\b', text_lower):
            return "Troubleshooting Guide"
        elif re.search(APP_SOFTWARE_PATTERNS["keywords"], text_lower, re.IGNORECASE):
            return "Software Bulletin"
        return "Unknown"
    except Exception as e:
        log_error(logger, f"Document type identification error: {e}")
        return "Unknown"
