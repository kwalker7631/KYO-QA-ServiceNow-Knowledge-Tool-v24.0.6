import unittest
from pathlib import Path
try:
    import fitz
except ImportError:  # pragma: no cover - skip if PyMuPDF missing
    fitz = None
from kyoqa import ocr_utils

class TestOCRUtilsLogging(unittest.TestCase):
    def setUp(self):
        if fitz is None or not hasattr(fitz, "open") or not hasattr(fitz, "Document"):
            self.skipTest("PyMuPDF not installed")
        self.pdf_path = Path("test_sample.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello world")
        doc.save(self.pdf_path)
        doc.close()

    def tearDown(self):
        if self.pdf_path.exists():
            self.pdf_path.unlink()

    def test_extract_text_logging(self):
        with self.assertLogs(ocr_utils.logger.name, level="INFO") as cm:
            text = ocr_utils.extract_text_from_pdf(self.pdf_path)
        self.assertTrue(any("Starting text extraction" in msg for msg in cm.output))
        self.assertTrue(any("Finished text extraction" in msg for msg in cm.output))
        self.assertEqual(text.strip(), "Hello world")

if __name__ == "__main__":
    unittest.main()
