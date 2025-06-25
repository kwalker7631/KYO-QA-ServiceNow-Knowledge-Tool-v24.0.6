# KYO QA ServiceNow Logging Utilities - REPAIRED
from version import VERSION
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Define Log Directory correctly relative to the project folder
LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Define the log file name once when the module is imported
SESSION_LOG_FILE = LOG_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_session.log"

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Sets up a logger that writes to a single session log file and the console.
    """
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Get the root logger, which will be the parent of all other loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Add handlers only once to the root logger
    if not root_logger.handlers:
        # File handler (writes to the single session file)
        file_handler = RotatingFileHandler(
            SESSION_LOG_FILE,
            maxBytes=10*1024*1024, # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        root_logger.info(f"Logging initialized for session. Log file: {SESSION_LOG_FILE}")

    # Return a specific logger for the module, which is a child of the root
    return logging.getLogger(name)

def log_info(logger: logging.Logger, message: str) -> None:
    logger.info(message)

def log_error(logger: logging.Logger, message: str) -> None:
    logger.error(message)

def log_warning(logger: logging.Logger, message: str) -> None:
    logger.warning(message)

def log_exception(logger: logging.Logger, message: str) -> None:
    logger.exception(message)

def create_success_log(message, output_file=None):
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_SUCCESSlog.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# KYO QA Tool Success Log - {VERSION}\n\n")
        f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        f.write("## Summary\n\n")
        f.write(message + "\n\n")
    return str(output_file)

def create_failure_log(message, error_details, output_file=None):
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_FAILlog.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# KYO QA Tool Failure Log - {VERSION}\n\n")
        f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        f.write("## Error Summary\n\n")
        f.write(message + "\n\n")
        f.write("## Technical Details\n\n")
        f.write("```\n")
        f.write(str(error_details))
        f.write("\n```\n")
    return str(output_file)