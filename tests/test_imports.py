import unittest

class ImportTests(unittest.TestCase):
    def test_package_imports(self):
        from extract import ai_extract
        from transform import process_files
        from format import generate_excel
        from utils import ensure_folders
        self.assertTrue(callable(ai_extract))
        self.assertTrue(callable(process_files))
        self.assertTrue(callable(generate_excel))
        self.assertTrue(callable(ensure_folders))

if __name__ == "__main__":
    unittest.main()
