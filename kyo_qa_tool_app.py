# KYO QA ServiceNow Tool - FINAL BRIGHT THEME VERSION
from version import VERSION
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import re, time, threading, sys, os

# --- Safe Import with Fallbacks ---
try:
    from processing_engine import process_files, process_pdf_list
    from file_utils import ensure_folders, cleanup_temp_files, open_file, is_file_locked
    from custom_exceptions import FileLockError
    from logging_utils import setup_logger
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False; print(f"WARNING: A backend module is missing, running in fallback mode. Error: {e}")
    class FileLockError(Exception): pass
    def process_files(f, e, t, p, s, o, c): return None, [], 0
    def process_pdf_list(f, e, t, p, s, o, c): return None, [], 0
    def ensure_folders(): pass;
    def cleanup_temp_files(): pass
    def open_file(p): return True
    def setup_logger(n): import logging; logging.basicConfig(level=logging.INFO); return logging.getLogger(n)

logger = setup_logger("app")

# --- NEW: Brighter Color Theme using Kyocera Standards ---
BRAND_COLORS = {
    "kyocera_red": "#E30613",
    "kyocera_black": "#231F20",
    "background": "#FFFFFF",
    "frame_background": "#F5F5F5",
    "header_text": "#000000",
    "accent_blue": "#0A9BCD",
    "success_green": "#00B176",
    "warning_yellow": "#F5B400",
}

class KyoQAToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # --- Core App State & Variables ---
        self.is_processing = False
        self.cancel_event = threading.Event()
        self.result_file_path = None
        self.selected_folder = tk.StringVar()
        self.selected_files_list = []
        self.output_path = tk.StringVar(value=str(Path.cwd() / "output" / "kb_import_file.xlsx"))
        self.status_current_file = tk.StringVar(value="Idle")
        self.status_ocr = tk.StringVar(value="Idle")
        # --- Setup UI ---
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        ensure_folders()

    def _setup_window(self):
        self.title(f"Kyocera QA ServiceNow Knowledge Tool v{VERSION}")
        self.geometry("1100x750")
        self.minsize(950, 650)
        self.configure(bg=BRAND_COLORS["background"])
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BRAND_COLORS["background"])
        style.configure("TLabel", background=BRAND_COLORS["background"], foreground=BRAND_COLORS["kyocera_black"], font=("Segoe UI", 10))
        style.configure("Header.TFrame", background=BRAND_COLORS["background"])
        style.configure("Header.TLabel", background=BRAND_COLORS["background"], foreground=BRAND_COLORS["header_text"], font=("Segoe UI", 16, "bold"))
        style.configure("KyoceraLogo.TLabel", background=BRAND_COLORS["background"], foreground=BRAND_COLORS["kyocera_red"], font=("Arial Black", 22))
        style.configure("TButton", background=BRAND_COLORS["kyocera_black"], foreground="white", font=("Segoe UI", 10, "bold"), padding=5)
        style.map("TButton", background=[("active", BRAND_COLORS["kyocera_red"])])
        style.configure("Red.TButton", background=BRAND_COLORS["kyocera_red"], foreground="white")
        style.map("Red.TButton", background=[("active", "#B81525")])
        style.configure("Status.TLabel", font=("Segoe UI", 9), background=BRAND_COLORS["frame_background"])
        style.configure("Status.Header.TLabel", font=("Segoe UI", 9, "bold"), background=BRAND_COLORS["frame_background"])
        style.configure("Dark.TFrame", background=BRAND_COLORS["frame_background"])

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header with a thin bottom border for a clean look
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=(10, 10))
        header_frame.grid(row=0, column=0, sticky="ew")
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.pack(side="bottom", fill="x")
        ttk.Label(header_frame, text="KYOCERA", style="KyoceraLogo.TLabel").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(header_frame, text="QA ServiceNow Knowledge Tool", style="Header.TLabel").pack(side=tk.LEFT, padx=(15, 0))
        
        main_frame = ttk.Frame(self, padding=15)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        self._create_io_section(main_frame)
        self._create_process_controls(main_frame)
        self._create_status_and_log_section(main_frame)
        
    def _create_io_section(self, parent):
        io_frame = ttk.LabelFrame(parent, text="1. Select Input", padding=10)
        io_frame.grid(row=0, column=0, sticky="ew", pady=5)
        io_frame.columnconfigure(1, weight=1)
        
        ttk.Label(io_frame, text="Process Folder:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(io_frame, textvariable=self.selected_folder, width=80).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(io_frame, text="Browse...", command=self.browse_folder).grid(row=0, column=2, padx=5)
        
        ttk.Label(io_frame, text="Or Select Files:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.files_label = ttk.Label(io_frame, text="0 files selected")
        self.files_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Button(io_frame, text="Select...", command=self.browse_files).grid(row=1, column=2, padx=5)

    def _create_process_controls(self, parent):
        controls_frame = ttk.LabelFrame(parent, text="2. Process", padding=10)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=5)
        controls_frame.columnconfigure(0, weight=2)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)
        
        self.process_btn = ttk.Button(controls_frame, text="▶ START PROCESSING", command=self.start_processing, style="Red.TButton", padding=(10,8))
        self.process_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.open_result_btn = ttk.Button(controls_frame, text="📂 Open Last Result", command=self.open_result, state=tk.DISABLED)
        self.open_result_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.clear_btn = ttk.Button(controls_frame, text="✨ Clear Inputs", command=self.clear_all)
        self.clear_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

    def _create_status_and_log_section(self, parent):
        container = ttk.LabelFrame(parent, text="3. Live Status & Activity Log", padding=10)
        container.grid(row=2, column=0, sticky="nsew", pady=5)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        status_frame = ttk.Frame(container, style="Dark.TFrame", padding=10)
        status_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        status_frame.columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="Current File:", style="Status.Header.TLabel").grid(row=0, column=0, sticky="e", padx=5)
        ttk.Label(status_frame, textvariable=self.status_current_file, style="Status.TLabel", anchor="w").grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(status_frame, text="OCR Status:", style="Status.Header.TLabel").grid(row=1, column=0, sticky="e", padx=5)
        ttk.Label(status_frame, textvariable=self.status_ocr, style="Status.TLabel").grid(row=1, column=1, sticky="w", padx=5)
        
        self.progress_bar = ttk.Progressbar(status_frame, orient='horizontal', mode='determinate')
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(10,5))
        
        self.log_text = tk.Text(container, height=8, wrap=tk.WORD, state=tk.DISABLED, bg="white", relief="solid", borderwidth=1, font=("Consolas", 9))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar = ttk.Scrollbar(container, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", padx=5, pady=5)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        for tag, color_key in [("info", "accent_blue"), ("success", "success_green"), ("warning", "warning_yellow"), ("error", "kyocera_red")]:
            self.log_text.tag_configure(tag, foreground=BRAND_COLORS[color_key])

    def _process_worker(self):
        try:
            excel_path = str(Path.cwd() / "output" / "kb_import_file.xlsx")
            
            def status_callback(file, stage):
                self.after(0, self.status_current_file.set, file)
                if stage == "OCR": self.after(0, self.status_ocr.set, "ACTIVE")
                elif stage == "DONE": self.after(0, self.status_ocr.set, "Idle")

            def progress_callback(message):
                self.after(0, self.log_message, message)
                match = re.search(r"(\d+)/(\d+)", message)
                if match: self.after(0, self.progress_bar.config, {"value": (int(match.group(1)) / int(match.group(2))) * 100})

            process_func = process_files if self.selected_folder.get() else process_pdf_list
            process_args = [self.selected_folder.get() or self.selected_files_list, excel_path, None, progress_callback, status_callback, lambda:None, self.cancel_event]
            
            result_path, _, _ = process_func(*process_args)

            self.result_file_path = result_path
            if self.cancel_event.is_set(): self.log_message("Processing cancelled by user.", "warning")
            elif result_path:
                self.log_message(f"Processing complete! Output saved to: {result_path}", "success")
                if messagebox.askyesno("Processing Complete", f"Success! Output saved to:\n{result_path}\n\nWould you like to open the file?"):
                    self.open_result()
        except FileLockError as e: messagebox.showwarning("File In Use", str(e))
        except Exception as e: self.handle_error("Processing Failed", f"A critical error occurred: {e}")
        finally:
            self.after(0, self.update_ui_for_processing, False)
            self.after(0, self.progress_bar.config, {"value": 0})

    def update_ui_for_processing(self, processing: bool):
        state = tk.DISABLED if processing else tk.NORMAL
        self.process_btn.config(state=state)
        self.clear_btn.config(state=state)
        self.status_current_file.set("Processing..." if processing else "Idle")
        self.status_ocr.set("Idle")
        if not processing: self.open_result_btn.config(state=tk.NORMAL if self.result_file_path else tk.DISABLED)

    def start_processing(self):
        if not self.selected_folder.get() and not self.selected_files_list: return messagebox.showwarning("Input Missing", "Please select a folder or PDF files.")
        self.update_ui_for_processing(True)
        threading.Thread(target=self._process_worker, daemon=True).start()

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder: self.selected_folder.set(folder); self.selected_files_list.clear(); self.files_label.config(text="0 files selected")
    
    def browse_files(self):
        files = filedialog.askopenfilenames(title="Select PDF Files", filetypes=[("PDF Files", "*.pdf;*.zip")])
        if files: self.selected_files_list = list(files); self.files_label.config(text=f"{len(files)} file(s) selected"); self.selected_folder.set("")

    def clear_all(self):
        self.selected_folder.set(""); self.selected_files_list.clear(); self.files_label.config(text="0 files selected")
        self.result_file_path = None; self.open_result_btn.config(state=tk.DISABLED); self.log_message("Inputs cleared.", "info")

    def open_result(self):
        if self.result_file_path and Path(self.result_file_path).exists(): open_file(self.result_file_path)
        else: messagebox.showwarning("File Not Found", "The result file does not exist.")

    def log_message(self, msg: str, tag: str = None):
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except: pass
        
    def handle_error(self, title, message):
        logger.error(f"{title}: {message}", exc_info=True)
        self.log_message(f"ERROR: {message}", "error")
        messagebox.showerror(title, message)

    def on_closing(self):
        if self.is_processing and messagebox.askyesno("Exit Confirmation", "Processing is in progress. Are you sure you want to exit?"):
            self.cancel_event.set()
        self.destroy()

if __name__ == "__main__":
    app = KyoQAToolApp()
    app.mainloop()