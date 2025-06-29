# data_harvesters.py
import re
from pathlib import Path

#==============================================================
# --- NEW FEATURE: Load patterns from default and custom files ---
#==============================================================
from config import (
    MODEL_PATTERNS as DEFAULT_MODEL_PATTERNS,
    QA_NUMBER_PATTERNS as DEFAULT_QA_PATTERNS,
    SHORT_QA_PATTERN, DATE_PATTERNS, SUBJECT_PATTERNS, 
    STANDARDIZATION_RULES, AUTHOR_PATTERNS, UNWANTED_AUTHORS, EXCLUSION_PATTERNS
)

# Try to import user-defined custom patterns. If the file doesn't exist, use empty lists.
try:
    from custom_patterns import (
        MODEL_PATTERNS as CUSTOM_MODEL_PATTERNS,
        QA_NUMBER_PATTERNS as CUSTOM_QA_PATTERNS
    )
except ImportError:
    CUSTOM_MODEL_PATTERNS = []
    CUSTOM_QA_PATTERNS = []

# Combine the lists, ensuring no duplicates. Custom patterns are added first to take precedence.
MODEL_PATTERNS = CUSTOM_MODEL_PATTERNS + [p for p in DEFAULT_MODEL_PATTERNS if p not in CUSTOM_MODEL_PATTERNS]
QA_NUMBER_PATTERNS = CUSTOM_QA_PATTERNS + [p for p in DEFAULT_QA_PATTERNS if p not in CUSTOM_QA_PATTERNS]
#==============================================================
# --- END OF NEW FEATURE ---
#==============================================================


def clean_model_string(model_str: str) -> str:
    for rule, replacement in STANDARDIZATION_RULES.items():
        model_str = model_str.replace(rule, replacement)
    return model_str.strip()

def is_excluded(text: str) -> bool:
    for pattern in EXCLUSION_PATTERNS:
        if pattern.lower() in text.lower():
            return True
    return False

def harvest_models_from_text(text: str) -> set:
    found_models = set()
    for pattern in MODEL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if not is_excluded(match):
                cleaned_match = clean_model_string(match)
                found_models.add(cleaned_match)
    return found_models

def harvest_models_from_filename(filename: str) -> set:
    found_models = set()
    for pattern in MODEL_PATTERNS:
        search_text = filename.replace("_", " ")
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            if not is_excluded(match):
                cleaned_match = clean_model_string(match)
                found_models.add(cleaned_match)
    return found_models

def harvest_qa_number(text: str) -> str:
    for pattern in QA_NUMBER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""

def harvest_short_qa_number(full_qa_number: str) -> str:
    if full_qa_number:
        match = re.search(SHORT_QA_PATTERN, full_qa_number)
        if match:
            return match.group(1).strip()
    return ""

def harvest_date(text: str) -> str:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""

def harvest_subject(text: str) -> str:
    for pattern in SUBJECT_PATTERNS:
        match = re.search(pattern, text)
        if match and match.group(1):
            return match.group(1).strip()
    return ""

def harvest_author(text: str) -> str:
    for pattern in AUTHOR_PATTERNS:
        match = re.search(pattern, text)
        if match and match.group(1):
            author = match.group(1).strip()
            if author in UNWANTED_AUTHORS:
                return ""
            return author
    return ""

def harvest_all_data(text: str, filename: str) -> dict:
    models_from_text = harvest_models_from_text(text)
    models_from_filename = harvest_models_from_filename(filename)
    all_found_models = sorted(list(models_from_text.union(models_from_filename)))
    full_qa = harvest_qa_number(text)
    short_qa = harvest_short_qa_number(full_qa)
    published_date = harvest_date(text)
    subject = harvest_subject(text)
    author = harvest_author(text)
    desc_parts = [part for part in [full_qa, subject] if part]
    short_description = ", ".join(desc_parts)
    models_str = ", ".join(all_found_models) if all_found_models else "Not Found"

    return {
        "models": models_str,
        "full_qa_number": full_qa,
        "short_qa_number": short_qa,
        "published_date": published_date,
        "subject": subject if subject else "No Subject Found",
        "author": author,
        "short_description": short_description
    }