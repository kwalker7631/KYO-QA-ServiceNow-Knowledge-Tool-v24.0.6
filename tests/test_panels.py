import unittest
from kyo_qa_tool_app import ProgressPanel, LogPanel
import tkinter as tk

class PanelTests(unittest.TestCase):
    def test_progress_panel_init(self):
        try:
            root = tk.Tk()
            root.withdraw()
        except tk.TclError:
            self.skipTest("No display available")
        panel = ProgressPanel(root)
        panel.show(1)
        self.assertTrue(hasattr(panel, 'progress'))
        root.destroy()

    def test_log_panel(self):
        try:
            root = tk.Tk()
            root.withdraw()
        except tk.TclError:
            self.skipTest("No display available")
        panel = LogPanel(root)
        panel.log_message('test', 'info')
        content = panel.log_text.get('1.0', tk.END)
        self.assertIn('test', content)
        root.destroy()

if __name__ == '__main__':
    unittest.main()
