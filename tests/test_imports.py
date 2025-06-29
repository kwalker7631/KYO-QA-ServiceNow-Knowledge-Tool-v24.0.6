import importlib
import os
import sys
import pytest
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

MODULES = ['custom_exceptions', 'file_utils', 'ocr_utils']


def test_modules_importable():
    for mod in MODULES:
        if mod == 'ocr_utils':
            pytest.importorskip('fitz')
        importlib.import_module(mod)


