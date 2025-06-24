import importlib


def test_ui_modules_importable():
    main_window = importlib.import_module('ui.main_window')
    widgets = importlib.import_module('ui.widgets')
    assert hasattr(main_window, 'KyoQAToolApp')
    assert hasattr(main_window, 'launch_app_with_splash')
    assert hasattr(widgets, 'SafeProgressFrame')
