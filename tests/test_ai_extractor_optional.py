import importlib
import builtins
import sys

import pytest


def test_ai_extractor_handles_missing_extract(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'extract.ai_extractor':
            raise ImportError('mock missing')
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', fake_import)

    if 'ai_extractor' in sys.modules:
        del sys.modules['ai_extractor']

    ai_extractor = importlib.import_module('ai_extractor')
    assert ai_extractor.QAExtractor is None
    with pytest.raises(ImportError):
        ai_extractor.ai_extract('text', None)

    monkeypatch.setattr(builtins, '__import__', original_import)

