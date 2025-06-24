import unittest


class TestLambdaExceptionCapture(unittest.TestCase):
    def test_capture_exception_in_lambda(self):
        try:
            raise ValueError("first")
        except Exception as e:
            def func(e=e):
                return f"error: {e}"
            e = ValueError("second")
        self.assertEqual(func(), "error: first")


if __name__ == "__main__":
    unittest.main()
