# flake8: noqa
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import unittest
from version import get_version


class TestVersion(unittest.TestCase):
    def test_get_version(self):
        self.assertEqual(get_version(), "24.0.6")


if __name__ == "__main__":
    unittest.main()
