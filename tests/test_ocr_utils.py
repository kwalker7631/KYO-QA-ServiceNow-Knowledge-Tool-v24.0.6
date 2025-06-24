import unittest
from pathlib import Path
import fitz
import ocr_utils

class TestOCRUtilsLogging(unittest.TestCase):
    def setUp(self):
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
        self.assertTrue(
            any("Starting text extraction" in msg for msg in cm.output)
        )
        self.assertTrue(
            any("Finished text extraction" in msg for msg in cm.output)
        )
        self.assertEqual(text.strip(), "Hello world")

    def test_init_tesseract_handles_missing(self):
        """init_tesseract should return False if pytesseract is unavailable."""
        original_exists = ocr_utils.os.path.exists
        original_popen = ocr_utils.os.popen
        ocr_utils.os.path.exists = lambda path: False

        class Dummy:
            def read(self):
                return ""

        ocr_utils.os.popen = lambda *args, **kwargs: Dummy()
        sys_modules = dict(ocr_utils.sys.modules)
        ocr_utils.sys.modules.pop("pytesseract", None)
        try:
            result = ocr_utils.init_tesseract()
            self.assertFalse(result)
        finally:
            ocr_utils.os.path.exists = original_exists
            ocr_utils.os.popen = original_popen
            ocr_utils.sys.modules.update(sys_modules)

if __name__ == "__main__":
    unittest.main()
