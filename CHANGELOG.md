		  # CHANGELOG

## v24.0.1 (2024-06-20)
- Refactored to fully modular, maintainable codebase with clear separation of GUI, OCR, AI extraction, file handling, and Excel output.
- Added vigorous logging to every module and process.
- Unified logging via `logging_utils.py`; logs named by date in `/logs/`.
- Subfolders auto-created on first run for logs/output.
- README and requirements updated for Python 3.11.x and latest packages.
- Every file and log stamped with version.
- Ready for robust testing, extension, and team deployment.

## v24.0.2 (2024-06-21)
- Introduced basic unit tests and GitHub workflow for continuous integration.
- Enhanced logging statements throughout the codebase.

## v24.0.3 (2024-06-22)
- Consolidated the startup script to handle package installation automatically.
- Improved CI configuration and exception handling.

## v24.0.4 (2024-06-23)
- Refactored extraction logic into a dedicated `QAExtractor` class.
- Removed unused imports and tightened error handling.

## v24.0.5 (2024-06-24)
- Added Excel formatting support and corresponding tests.
- Optimized modules and cleaned obsolete directories.

## v24.0.6 (2024-06-25)
- Added fallback for missing Excel templates.
- General code cleanup and formatting fixes.
