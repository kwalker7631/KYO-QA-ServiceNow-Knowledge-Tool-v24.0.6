from tkinter import ttk
import tkinter as tk
import pytest
from gui.widgets import SafeProgressFrame


def test_safe_progress_frame_creation():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tkinter unavailable")
    frame = SafeProgressFrame(root)
    assert isinstance(frame.progress, ttk.Progressbar)
    root.destroy()
