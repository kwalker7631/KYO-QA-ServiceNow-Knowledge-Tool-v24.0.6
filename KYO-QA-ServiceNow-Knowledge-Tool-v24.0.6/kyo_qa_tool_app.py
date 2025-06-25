# KYO QA ServiceNow Tool - FINAL VERSION with Brand UI
from version import VERSION
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import threading
import time
from pathlib import Path
import re

# --- Safe Import with Fallbacks ---
try:
    from processing_engine import process_files, process_pdf_list
    from file_utils import ensure_folders, cleanup_temp_files, open_file, is_file_locked
    from custom_exceptions import FileLockError
    from logging_utils import setup_logger, log_info, log_error, log_exception, LOG_DIR
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    class FileLockError(Exception): pass
    def process_files(f, e, t, p, o, c): return None, [], 0
    def process_pdf_list(f, e, t, p, o, c): return None, [], 0
    def ensure_folders(): pass
    def cleanup_temp_files(): pass
    def open_file(p): return True
    def setup_logger(n): import logging; logging.basicConfig(level=logging.INFO); return logging.getLogger(n)
    LOG_DIR = Path.cwd() / "logs"

logger = setup_logger("app")

# --- NEW: Official Kyocera Brand Colors ---
BRAND_COLORS = {
    "kyocera_red": "#E31A2F",
    "kyocera_black": "#231F20",
    "kyocera_dark_grey": "#282828",
    "kyocera_light_grey": "#F2F2F2",
    "accent_blue": "#0A9BCD",
    "accent_purple": "#6E3CBE",
    "success": "#00B176",
    "warning": "#F5B400",
}

class KyoQAToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # --- Core Application State ---
        self.is_processing = False
        self.cancel_event = threading.Event()
        self.result_file_path = None
        # --- Initialize Tkinter Variables ---
        self.selected_folder = tk.StringVar()
        self.selected_files_list = []
        self.output_path = tk.StringVar(value=str(Path.cwd() / "output" / "kb_import_file.xlsx"))
        # --- Setup UI ---
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self._initialize_app_core()

    def _setup_window(self):
        self.title(f"Kyocera QA ServiceNow Knowledge Tool v{VERSION}")
        self.geometry("1024x768")
        self.minsize(900, 650)
        self.configure(bg=BRAND_COLORS["kyocera_light_grey"])
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        # --- Style Updates using Brand Colors ---
        style.configure("TFrame", background=BRAND_COLORS["kyocera_light_grey"])
        style.configure("TLabel", background=BRAND_COLORS["kyocera_light_grey"], foreground=BRAND_COLORS["kyocera_black"])
        style.configure("Header.TFrame", background=BRAND_COLORS["kyocera_black"])
        style.configure("Header.TLabel", background=BRAND_COLORS["kyocera_black"], foreground=BRAND_COLORS["kyocera_light_grey"], font=("Segoe UI", 16, "bold"))
        style.configure("KyoceraLogo.TLabel", background=BRAND_COLORS["kyocera_black"], foreground=BRAND_COLORS["kyocera_red"], font=("Arial Black", 20, "bold"))
        style.configure("TButton", background=BRAND_COLORS["accent_blue"], foreground="white", font=("Segoe UI", 10, "bold"), padding=5, borderwidth=0)
        style.map("TButton", background=[("active", BRAND_COLORS["accent_purple"])])
        style.configure("Red.TButton", background=BRAND_COLORS["kyocera_red"], foreground="white")
        style.map("Red.TButton", background=[("active", "#B81525")])

    def _initialize_app_core(self):
        ensure_folders()
        cleanup_temp_files()
        self.log_message(f"Application v{VERSION} initialized. Ready to process files.", "info")

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        # --- UI FEATURE: New Header ---
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=(10, 5))
        header_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(header_frame, text="KYOCERA", style="KyoceraLogo.TLabel").pack(side=tk.LEFT, padx=(5, 0), pady=5)
        ttk.Label(header_frame, text="QA ServiceNow Knowledge Tool", style="Header.TLabel").pack(side=tk.LEFT, padx=(10, 0), pady=5)
        ttk.Label(header_frame, text=f"v{VERSION}", background=BRAND_COLORS["kyocera_black"], foreground="white", font=("Segoe UI", 10)).pack(side=tk.RIGHT, padx=10)
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        self._create_io_section(main_frame)
        self._create_process_controls(main_frame)
        self._create_log_section(main_frame)
        
        status_bar = ttk.Frame(self, padding=(5,2), relief="sunken")
        status_bar.grid(row=2, column=0, sticky="ew")
        self.status_label = ttk.Label(status_bar, text="Ready.")
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.ocr_indicator_label = ttk.Label(status_bar, text="OCR Active", font=("Segoe UI", 10, "bold"), foreground=BRAND_COLORS["warning"])
        ttk.Button(status_bar, text="Exit", command=self.on_closing, width=10).pack(side=tk.RIGHT, padx=5)

    def _create_io_section(self, parent):
        io_frame = ttk.LabelFrame(parent, text="1. Input & Output", padding=10)
        io_frame.grid(row=0, column=0, sticky="ew", pady=5)
        io_frame.columnconfigure(1, weight=1)
        ttk.Label(io_frame, text="Input Folder:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(io_frame, textvariable=self.selected_folder, width=80).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(io_frame, text="Browse...", command=self.browse_folder).grid(row=0, column=2, padx=5)
        ttk.Label(io_frame, text="Or Select Files:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.files_label = ttk.Label(io_frame, text="0 files selected", style="TLabel")
        self.files_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Button(io_frame, text="Select...", command=self.browse_files).grid(row=1, column=2, padx=5)
        ttk.Label(io_frame, text="Excel Output:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(io_frame, textvariable=self.output_path, width=80).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(io_frame, text="Browse...", command=self.browse_output).grid(row=2, column=2, padx=5)

    def _create_process_controls(self, parent):
        controls_frame = ttk.LabelFrame(parent, text="2. Controls", padding=10)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=5)
        controls_frame.columnconfigure(list(range(4)), weight=1)
        # --- UI FEATURE: Using the red brand color for the main action button ---
        self.process_btn = ttk.Button(controls_frame, text="▶ Start Processing", command=self.start_processing, style="Red.TButton")
        self.process_btn.grid(row=0, column=0, padx=5, sticky="ew")
        self.cancel_btn = ttk.Button(controls_frame, text="■ Cancel", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_btn.grid(row=0, column=1, padx=5, sticky="ew")
        self.open_result_btn = ttk.Button(controls_frame, text="📂 Open Result", command=self.open_result, state=tk.DISABLED)
        self.open_result_btn.grid(row=0, column=2, padx=5, sticky="ew")
        self.clear_btn = ttk.Button(controls_frame, text="✨ Clear All", command=self.clear_all)
        self.clear_btn.grid(row=0, column=3, padx=5, sticky="ew")

    def _create_log_section(self, parent):
        log_frame = ttk.LabelFrame(parent, text="3. Activity Log", padding=10)
        log_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        self.progress_bar = ttk.Progressbar(log_frame, orient='horizontal', mode='determinate')
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(0,5))
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED, bg="white", relief="solid", borderwidth=1, font=("Segoe UI", 9))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=5)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)
        for tag, color in [("info", BRAND_COLORS["accent_blue"]), ("success", BRAND_COLORS["success"]), ("warning", BRAND_COLORS["warning"]), ("error", BRAND_COLORS["kyocera_red"])]:
            self.log_text.tag_configure(tag, foreground=color)

    def set_ocr_indicator(self, is_active):
        if is_active: self.ocr_indicator_label.pack(side=tk.LEFT, padx=10)
        else: self.ocr_indicator_label.pack_forget()

    def _process_worker(self):
        try:
            excel_path = self.output_path.get()
            def progress_callback(message):
                self.after(0, self.log_message, message)
                match = re.search(r"(\d+)/(\d+)", message)
                if match: self.after(0, self.progress_bar.config, {"value": (int(match.group(1)) / int(match.group(2))) * 100})
            def ocr_callback(is_active): self.after(0, self.set_ocr_indicator, is_active)
            
            if self.selected_folder.get():
                result_path, _, _ = process_files(self.selected_folder.get(), excel_path, None, progress_callback, ocr_callback, self.cancel_event)
            else:
                result_path, _, _ = process_pdf_list(self.selected_files_list, excel_path, None, progress_callback, ocr_callback, self.cancel_event)
            
            self.result_file_path = result_path
            if self.cancel_event.is_set(): self.log_message("Processing was cancelled.", "warning")
            elif result_path:
                self.log_message("Processing completed successfully!", "success")
                messagebox.showinfo("Processing Complete", f"Processing has finished.\nOutput file saved to:\n{result_path}")
        except FileLockError as e:
            self.log_message(f"File is locked. Please close the Excel file and try again.", "error")
            messagebox.showwarning("File In Use", str(e))
        except Exception as e:
            self.handle_error("Processing Failed", f"A critical error occurred: {e}")
        finally:
            self.after(0, self.update_ui_for_processing, False)
            self.after(0, self.progress_bar.config, {"value": 0})

    def start_processing(self):
        if not self.selected_folder.get() and not self.selected_files_list: return messagebox.showwarning("Input Missing", "Please select a folder or PDF files.")
        self.update_ui_for_processing(True)
        threading.Thread(target=self._process_worker, daemon=True).start()

    def update_ui_for_processing(self, processing: bool):
        state = tk.DISABLED if processing else tk.NORMAL
        self.process_btn.config(state=state)
        self.clear_btn.config(state=state)
        self.cancel_btn.config(state=tk.NORMAL if processing else tk.DISABLED)
        self.status_label.config(text="Processing..." if processing else "Ready.")
        if not processing: self.open_result_btn.config(state=tk.NORMAL if self.result_file_path else tk.DISABLED)

    def log_message(self, msg: str, tag: str = None):
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except: pass
        
    def handle_error(self, title, message):
        log_error(logger, f"{title}: {message}")
        self.log_message(f"ERROR: {message}", "error")
        messagebox.showerror(title, message)

    def on_closing(self):
        if self.is_processing and messagebox.askyesno("Exit Confirmation", "Processing is still in progress. Are you sure you want to exit?"):
            self.cancel_event.set()
        self.destroy()

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder: self.selected_folder.set(folder); self.selected_files_list.clear(); self.files_label.config(text="0 files selected")
    def browse_files(self):
        files = filedialog.askopenfilenames(title="Select PDF Files", filetypes=[("PDF Files", "*.pdf")])
        if files: self.selected_files_list = list(files); self.files_label.config(text=f"{len(self.selected_files_list)} file(s) selected"); self.selected_folder.set("")
    def browse_output(self):
        path = filedialog.asksaveasfilename(title="Save As", defaultextension=".xlsx", initialfile="kb_import_file.xlsx")
        if path: self.output_path.set(path)
    def open_result(self):
        if self.result_file_path and Path(self.result_file_path).exists(): open_file(self.result_file_path)
        else: messagebox.showwarning("File Not Found", "The result file does not exist.")
    def cancel_processing(self):
        self.cancel_event.set()
    def clear_all(self):
        self.selected_folder.set(""); self.selected_files_list.clear(); self.files_label.config(text="0 files selected")
        self.result_file_path = None; self.open_result_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = KyoQAToolApp()
    app.mainloop()