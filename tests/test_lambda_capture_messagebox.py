import unittest


class TestLambdaExceptionCaptureMessageBox(unittest.TestCase):
    def test_capture_exception_in_messagebox_lambda(self):
        try:
            raise RuntimeError("one")
        except Exception as e:
            def func(e=e):
                return f"Error: {e}"
            e = RuntimeError("two")
        self.assertEqual(func(), "Error: one")


if __name__ == "__main__":
    unittest.main()
