# ai_extractor.py - Minimal AI extraction module
from logging_utils import setup_logger, log_info, log_error

logger = setup_logger("ai_extractor")

def extract_with_ai(text: str, prompt: str = None) -> str:
    """
    Placeholder for AI-based text extraction.
    In production, this would use ollama or another AI service.
    """
    log_info(logger, "AI extraction called (placeholder implementation)")
    
    # For now, just return empty string to prevent errors
    # Replace with actual AI implementation when ready
    return ""

def is_ai_available() -> bool:
    """Check if AI service is available."""
    try:
        import ollama
        # You could add actual availability check here
        return True
    except ImportError:
        log_error(logger, "Ollama not installed - AI features disabled")
        return False