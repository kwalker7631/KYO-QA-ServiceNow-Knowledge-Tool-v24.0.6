# KYO QA ServiceNow Logging Utilities
from version import VERSION

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Create logs directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str, console_output=True, max_file_size=10*1024*1024) -> logging.Logger:
    """
    Return a logger that writes to both a dated log file and console if requested.
    
    Args:
        name: Logger name
        console_output: Whether to output to console
        max_file_size: Maximum log file size in bytes before rotation (default 10MB)
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Return existing logger if already configured
    if logger.handlers:
        return logger
    
    # Set level
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler with rotation
    log_file = LOG_DIR / f"{datetime.now():%Y%m%d}_{name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add version info to the log
    logger.info(f"Logger initialized: {name} - {VERSION}")
    
    return logger

def log_info(logger: logging.Logger, message: str) -> None:
    """Log an info message."""
    logger.info(message)

def log_error(logger: logging.Logger, message: str) -> None:
    """Log an error message."""
    logger.error(message)

def log_warning(logger: logging.Logger, message: str) -> None:
    """Log a warning message."""
    logger.warning(message)

def log_debug(logger: logging.Logger, message: str) -> None:
    """Log a debug message."""
    logger.debug(message)

def log_critical(logger: logging.Logger, message: str) -> None:
    """Log a critical message."""
    logger.critical(message)

def log_safe(logger: logging.Logger, message: str, level: str = "info", max_length: int = 250) -> None:
    """Log a message safely by stripping newlines and truncating large blocks.

    Args:
        logger: Logger instance to use.
        message: The text to log.
        level: Logging level name (default ``info``).
        max_length: Maximum characters to log before truncating.
    """
    clean = message.replace("\n", " ").replace("\r", " ")
    if len(clean) > max_length:
        clean = clean[:max_length] + "..."
    getattr(logger, level, logger.info)(clean)

def log_exception(logger: logging.Logger, message: str) -> None:
    """Log an exception with traceback."""
    logger.exception(message)

def create_success_log(message, output_file=None):
    """Create a summary success log file."""
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_SUCCESSlog.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# KYO QA Tool Success Log - {VERSION}\n\n")
        f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        f.write("## Summary\n\n")
        f.write(message + "\n\n")
        f.write("---\n\n")
        f.write("Process completed successfully.\n")
    
    return str(output_file)

def create_failure_log(message, error_details, output_file=None):
    """Create a summary failure log file."""
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_FAILlog.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# KYO QA Tool Failure Log - {VERSION}\n\n")
        f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        f.write("## Error Summary\n\n")
        f.write(message + "\n\n")
        f.write("## Technical Details\n\n")
        f.write("```\n")
        f.write(error_details)
        f.write("\n```\n\n")
        f.write("---\n\n")
        f.write("Please check the detailed logs for more information.\n")
    
    return str(output_file)
