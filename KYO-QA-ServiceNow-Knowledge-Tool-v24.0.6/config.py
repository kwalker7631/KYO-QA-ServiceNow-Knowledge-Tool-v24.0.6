# KYO QA ServiceNow Configuration for Adaptable Standardization
from version import VERSION

# QA Number Extraction Patterns
QA_NUMBER_PATTERNS = [
    r"(QA|SB)?[-_]?([A-Z0-9]+[-_][0-9]+)\s*\((P?\d{3,5})\)",  # e.g., QA_2NJ-0015_(P008)
    r"(QA|SB)?[-_]?([A-Z0-9]+[-_][0-9]+)",  # e.g., QA_2NJ-0015
    r"(QA|SB)?[-_]?([A-Z0-9]+[-_]?[0-9]+)",  # e.g., QA_2Z7-0009
    r"(QA|SB)?[-_]?(\d{3,5})",  # e.g., QA_K123
]

# Model Extraction Patterns
MODEL_PATTERNS = [
    r"\b(?:ECOSYS|TASKalfa|FS|KM|CS)[-\s]*[A-Za-z0-9]+\b",  # Standard models
    r"\b[a-zA-Z]+[0-9]+[a-zA-Z]*\b",  # Generic model-like patterns
]

# Date Extraction Patterns
DATE_PATTERNS = [
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+[0-9]{1,2}(?:st|nd|rd|th)?[\s,]+[0-9]{4}\b",
    r"\b[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}\b",  # e.g., 01/15/2025
    r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b",  # e.g., 2025-01-15
]

# Subject/Title Extraction Patterns
SUBJECT_PATTERNS = [
    r'(?:subject|title|summary|overview|abstract|issue|problem|symptom)s?[\s:]*([^\n]{10,1000})',
    r'^(?!.*(?:ECOSYS|TASKalfa|FS|KM|CS))[^\n]{10,500}',  # First non-model paragraph
]

# Standardization Rules
STANDARDIZATION_RULES = {
    "short_description_format": "{full_qa_number} {date} {subject}",
    "meta_description_format": "QA, {short_qa_number}",
    "default_author": "Knowledge Import",
    "default_workflow_state": "Work in Progress",
    "default_article_type": "HTML",
    "max_subject_length": 1000,
    "max_model_list_length": 32700,
    "default_date": "",  # Use empty string if no date found
}

# Application Software Bulletin Handling
APP_SOFTWARE_PATTERNS = {
    "keywords": r"\b(?:software|application|driver|utility|print\s+server|cloud)\b",
    "fallback_models": "Software Bulletin",  # Placeholder for bulletins without models
}
