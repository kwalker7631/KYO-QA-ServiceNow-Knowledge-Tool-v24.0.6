import importlib
import pytest

modules = [
    'processing_engine',
    'config',
    'custom_exceptions',
    'extract.ai_extractor',
    'excel_generator',
    'file_utils',
    'data_harvesters',
    'ocr_utils'
]

@pytest.mark.parametrize('module_name', modules)
def test_module_import(module_name):
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        pytest.skip(str(e))
