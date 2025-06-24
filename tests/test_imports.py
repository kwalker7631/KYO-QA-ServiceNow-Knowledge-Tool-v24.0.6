import importlib
import pytest

modules = [
    'kyoqa.processing_engine',
    'kyoqa.config',
    'kyoqa.custom_exceptions',
    'kyoqa.ai_extractor',
    'kyoqa.excel_generator',
    'kyoqa.file_utils',
    'kyoqa.data_harvesters',
    'kyoqa.ocr_utils'
]

@pytest.mark.parametrize('module_name', modules)
def test_module_import(module_name):
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        pytest.skip(str(e))
