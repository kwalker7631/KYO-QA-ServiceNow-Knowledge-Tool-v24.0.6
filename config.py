# KYO QA ServiceNow Configuration for Adaptable Standardization - FINAL VERSION
from version import VERSION

# --- Application Setup ---
REQUIRED_FOLDERS = ["logs", "output", "PDF_TXT", "temp"]

# --- NEW: Explicit Mapping from Harvested Data to Excel Headers ---
# This dictionary is what was missing. It ensures data keys always match your template.
HEADER_MAPPING = {
    # Internal Data Name : Exact Excel Column Header
    'active': 'Active',
    'article_type': 'Article type',
    'author': 'Author',
    'category': 'Category(category)',
    'confidence': 'Confidence',
    'description': 'Description',
    'disable_commenting': 'Disable commenting',
    'disable_suggesting': 'Disable suggesting',
    'display_attachments': 'Display attachments',
    'flagged': 'Flagged',
    'governance': 'Governance',
    'kb_category': 'Category(kb_category)',
    'knowledge_base': 'Knowledge base',
    'meta': 'Meta',
    'meta_description': 'Meta Description',
    'published_date': 'Published',
    'short_description': 'Short description',
    'topic': 'Topic',
    'models': 'models', # Note: lowercase 'm' as per your template
    'valid_to': 'Valid to',
    'change_type': 'Change Type',
    'revision': 'Revision',
    'file_name': 'file_name',
    'needs_review': 'needs_review',
    'processing_status': 'processing_status'
}


# --- Data Extraction Patterns ---
QA_NUMBER_PATTERNS = [
    r"Ref\.\s*No\.\s*([A-Z0-9]{2,}[-][0-9]+)\s*\(([A-Z]\d+)\)",
    r"\b([A-Z0-9]{2,}[-][0-9]+)\s*\(([A-Z]\d+)\)",
    r"Ref\.\s*No\.\s*([A-Z0-9]{2,}[-][0-9]+)",
    r"((E\d{3,}|[A-Z0-9]{2,})[-][A-Z0-9]{2,}[-][0-9]+)\b",
    r"([A-Z0-9]{2,}-\d{4})\b"
]
SHORT_QA_PATTERN = r"\(([A-Z]\d+)\)"
MODEL_PATTERNS = [
    r"Model[:\s]*\n*((?:(?:TASKalfa|ECOSYS|FS-C)\s+[A-Za-z0-9\s,/-]+)+)", 
    r"\b((?:TASKalfa|ECOSYS|FS-C)[\sA-Za-z0-9,/-]+)\b",
]
DATE_PATTERNS = [
    r"<Date>\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
    r"\b(\d{1,2}/\d{1,2}/\d{4})\b", r"\b(\d{4}-\d{2}-\d{2})\b",
]
SUBJECT_PATTERNS = [
    r'Subject\s*:\s*([^\n\r]+?)(?:\n\n|Model:|Classification:|timing:|Phenomenon:|Problem:|Cause:|Measure:|Remarks:|$)',
    r'Title\s*:\s*([^\n\r]+?)(?:\n\n|Model:|Classification:|timing:|Phenomenon:|Problem:|Cause:|Measure:|Remarks:|$)',
]
CHANGE_TYPE_PATTERNS = [
    r"Type\s+of\s+change[:\s\n]*.*?((Hardware|Firmware\s+and\s+Software|Information)\s*☑)",
    r"Type\s+of\s+change[:\s\n]*.*?(Hardware|Firmware\s+and\s+Software|Information)"
]

# --- Standardization Rules ---
STANDARDIZATION_RULES = {"default_author": "Knowledge Import"}
APP_SOFTWARE_PATTERNS = {
    "keywords": r"\b(?:software|application|driver|utility|print\s+server|cloud)\b",
    "fallback_models": "Software Bulletin",
}