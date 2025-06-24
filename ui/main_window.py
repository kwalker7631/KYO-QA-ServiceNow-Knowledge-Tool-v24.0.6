"""Main application window for the KYO QA Tool."""

import os
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from version import VERSION

from .widgets import (
    BRAND_COLORS,
    SafeGradientFrame,
    SafeColorSpinnerCanvas,
    SafeProgressFrame,
)

try:
    from processing_engine import process_files, process_pdf_list
    from file_utils import ensure_folders, cleanup_temp_files, open_file
    from logging_utils import (
        setup_logger,
        log_info,
        log_error,
        log_exception,
        create_success_log,
        create_failure_log,
        LOG_DIR,
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not found: {e}")
    MODULES_AVAILABLE = False

    def process_files(folder, excel_path, template_path, progress_cb, ocr_cb, cancel_event):
        import random
        files = random.randint(5, 10)
        for i in range(1, files + 1):
            if cancel_event.is_set():
                break
            if i % 3 == 0:
                ocr_cb(True)
            progress_cb(f"Processing file {i}/{files}: example_file_{i}.pdf")
            time.sleep(1.5)
            ocr_cb(False)
        return excel_path, ["review_doc.pdf"], max(0, random.randint(-1, 1))

    def process_pdf_list(files, excel_path, template_path, progress_cb, ocr_cb, cancel_event):
        for i, f in enumerate(files):
            if cancel_event.is_set():
                break
            if i % 2 == 0:
                ocr_cb(True)
            progress_cb(f"Processing file {i+1}/{len(files)}: {Path(f).name}")
            time.sleep(1.5)
            ocr_cb(False)
        return excel_path, [], 0

    def ensure_folders():
        pass

    def cleanup_temp_files():
        pass

    def open_file(path):
        return True

    def setup_logger(name):
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)

    def log_info(logger_obj, message):
        logger_obj.info(message)

    def log_error(logger_obj, message):
        logger_obj.error(message)

    def log_exception(logger_obj, message):
        logger_obj.exception(message)

    def create_success_log(m):
        pass

    def create_failure_log(m, d):
        pass

    LOG_DIR = Path.cwd() / "logs"

logger = setup_logger("app")


class KyoQAToolApp(tk.Tk):
    """Main Tkinter application."""

    def __init__(self):
        super().__init__()
        self.is_processing = False
        self.cancel_event = threading.Event()
        self.fullscreen = False
        self.result_file = None
        self._setup_window()
        self._setup_variables()
        try:
            self.setup_styles()
            self.create_widgets()
        except Exception as e:
            print(f"GUI setup error: {e}")
            self._create_fallback_gui()
        self._initialize_app()

    def _setup_window(self):
        try:
            self.title(f"Kyocera QA ServiceNow Knowledge Tool {VERSION}")
            self.configure(bg=BRAND_COLORS["background"])
            try:
                self.attributes("-fullscreen", True)
                self.fullscreen = True
            except Exception:
                self.state("zoomed")
                self.fullscreen = False
            try:
                base_path = getattr(sys, "_MEIPASS", Path(__file__).parent)
                icon_path = base_path / "kyo_icon.ico"
                if icon_path.exists():
                    self.iconbitmap(icon_path)
            except Exception:
                pass
        except Exception as e:
            print(f"Window setup error: {e}")
            self.geometry("900x700")

    def _setup_variables(self):
        try:
            self.selected_folder = tk.StringVar()
            self.selected_files = []
            self.selected_template = tk.StringVar()
            self.status_text = tk.StringVar(value="Ready to process files.")
            self.output_path = tk.StringVar(value=str(Path.cwd() / "output" / "kb_import_file.xlsx"))
        except Exception as e:
            print(f"Variable setup error: {e}")

    def setup_styles(self):
        try:
            self.style = ttk.Style(self)
            self.style.theme_use("clam")
            self.style.configure("TLabel", background=BRAND_COLORS["background"], foreground=BRAND_COLORS["text"])
            self.style.configure("TFrame", background=BRAND_COLORS["background"])
            self.style.configure("TButton", background=BRAND_COLORS["button"], foreground=BRAND_COLORS["button_text"])
            try:
                self.style.configure("Header.TFrame", background=BRAND_COLORS["header_bg"])
                self.style.configure("Header.TLabel", background=BRAND_COLORS["header_bg"], foreground=BRAND_COLORS["header_fg"], font=("Helvetica", 16, "bold"))
                self.style.configure("KyoceraLogo.TLabel", background=BRAND_COLORS["header_bg"], foreground=BRAND_COLORS["kyocera_red"], font=("Arial Black", 20, "bold"))
            except Exception as e:
                print(f"Advanced style setup error: {e}")
        except Exception as e:
            print(f"Style setup error: {e}")

    def create_widgets(self):
        try:
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self._create_header()
            self._create_main_content()
            self._create_status_bar()
        except Exception as e:
            print(f"Widget creation error: {e}")
            raise

    def _create_header(self):
        try:
            header_frame = ttk.Frame(self, style="Header.TFrame", padding=(10, 5))
            header_frame.grid(row=0, column=0, sticky="ew")
            ttk.Label(header_frame, text="KYOCERA", style="KyoceraLogo.TLabel").pack(side=tk.LEFT, padx=(5, 0))
            ttk.Label(header_frame, text="QA ServiceNow Knowledge Tool", style="Header.TLabel").pack(side=tk.LEFT, padx=(10, 0))
            ttk.Label(
                header_frame,
                text=f"v{VERSION}",
                background=BRAND_COLORS["header_bg"],
                foreground=BRAND_COLORS["header_fg"],
            ).pack(side=tk.RIGHT, padx=10)
        except Exception as e:
            print(f"Header creation error: {e}")

    def _create_main_content(self):
        try:
            main_frame = ttk.Frame(self, padding=10)
            main_frame.grid(row=1, column=0, sticky="nsew")
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(3, weight=1)
            self._create_io_section(main_frame)
            self._create_process_section(main_frame)
            self.progress_frame = SafeProgressFrame(main_frame)
            self.progress_frame.grid(row=2, column=0, sticky="ew", pady=5)
            self._create_log_section(main_frame)
        except Exception as e:
            print(f"Main content creation error: {e}")

    def _create_io_section(self, parent):
        try:
            io_frame = ttk.LabelFrame(parent, text="1. Select Inputs & Outputs", padding=10)
            io_frame.grid(row=0, column=0, sticky="ew", pady=5)
            io_frame.columnconfigure(1, weight=1)
            ttk.Label(io_frame, text="Process Folder:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
            ttk.Entry(io_frame, textvariable=self.selected_folder).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            ttk.Button(io_frame, text="📂 Browse...", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)
            ttk.Label(io_frame, text="Or Select PDFs:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
            self.files_label = ttk.Label(io_frame, text="No files selected", wraplength=400)
            self.files_label.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
            ttk.Button(io_frame, text="📄 Select...", command=self.browse_files).grid(row=1, column=2, padx=5, pady=5)
            ttk.Label(io_frame, text="Excel Output:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
            ttk.Entry(io_frame, textvariable=self.output_path).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
            ttk.Button(io_frame, text="💾 Browse...", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)
            ttk.Label(io_frame, text="Template (optional):").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
            ttk.Entry(io_frame, textvariable=self.selected_template).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
            ttk.Button(io_frame, text="📋 Browse...", command=self.browse_template).grid(row=3, column=2, padx=5, pady=5)
        except Exception as e:
            print(f"IO section creation error: {e}")

    def _create_process_section(self, parent):
        try:
            process_frame = ttk.LabelFrame(parent, text="2. Process Controls", padding=10)
            process_frame.grid(row=1, column=0, sticky="ew", pady=10)
            process_frame.columnconfigure(list(range(5)), weight=1)
            self.process_btn = ttk.Button(process_frame, text="▶ Start Processing", command=self.process)
            self.process_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            self.cancel_btn = ttk.Button(process_frame, text="■ Cancel", command=self.cancel_processing, state=tk.DISABLED)
            self.cancel_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            self.preview_btn = ttk.Button(process_frame, text="👀 Open Result", command=self.preview_result, state=tk.DISABLED)
            self.preview_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
            self.clear_btn = ttk.Button(process_frame, text="✨ Clear", command=self.clear_selection)
            self.clear_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
            self.logs_btn = ttk.Button(process_frame, text="📋 Logs", command=self.view_logs)
            self.logs_btn.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        except Exception as e:
            print(f"Process section creation error: {e}")

    def _create_log_section(self, parent):
        try:
            log_frame = ttk.LabelFrame(parent, text="Activity Log", padding=10)
            log_frame.grid(row=3, column=0, sticky="nsew", pady=5)
            log_frame.rowconfigure(0, weight=1)
            log_frame.columnconfigure(0, weight=1)
            text_frame = ttk.Frame(log_frame)
            text_frame.grid(row=0, column=0, sticky="nsew")
            text_frame.rowconfigure(0, weight=1)
            text_frame.columnconfigure(0, weight=1)
            self.log_text = tk.Text(text_frame, height=10, width=80, wrap=tk.WORD, bg="white", fg=BRAND_COLORS["text"], state=tk.DISABLED)
            self.log_text.grid(row=0, column=0, sticky="nsew")
            scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.log_text.config(yscrollcommand=scrollbar.set)
            try:
                self.log_text.tag_configure("success", foreground=BRAND_COLORS["success"])
                self.log_text.tag_configure("warning", foreground=BRAND_COLORS["warning"])
                self.log_text.tag_configure("error", foreground=BRAND_COLORS["error"])
                self.log_text.tag_configure("info", foreground=BRAND_COLORS["info"])
            except Exception:
                pass
        except Exception as e:
            print(f"Log section creation error: {e}")

    def _create_status_bar(self):
        try:
            status_frame = ttk.Frame(self, relief="sunken", padding=2)
            status_frame.grid(row=2, column=0, sticky="ew")
            self.status_label = ttk.Label(status_frame, textvariable=self.status_text)
            self.status_label.pack(side=tk.LEFT, padx=5)
            self.exit_btn = ttk.Button(status_frame, text="Exit", command=self.on_closing)
            self.exit_btn.pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            print(f"Status bar creation error: {e}")

    def _create_fallback_gui(self):
        try:
            for widget in self.winfo_children():
                widget.destroy()
            main_label = tk.Label(self, text=f"KYO QA Tool v{VERSION}", font=("Helvetica", 16), bg=BRAND_COLORS["background"])
            main_label.pack(pady=20)
            error_label = tk.Label(self, text="GUI Error - Using Fallback Mode", fg="red", bg=BRAND_COLORS["background"])
            error_label.pack(pady=10)
            tk.Button(self, text="Select Folder", command=self.browse_folder).pack(pady=5)
            tk.Button(self, text="Process", command=self.process).pack(pady=5)
            tk.Button(self, text="Exit", command=self.on_closing).pack(pady=5)
        except Exception as e:
            print(f"Fallback GUI creation error: {e}")

    def _initialize_app(self):
        try:
            self.bind("<Escape>", self.toggle_fullscreen)
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            ensure_folders()
            cleanup_temp_files()
            self.safe_log_message(f"Kyocera QA Tool v{VERSION} Initialized", "info")
            self.safe_log_message("Please select a folder or PDF files to begin.")
        except Exception as e:
            print(f"App initialization error: {e}")

    def safe_log_message(self, msg, tag=None):
        try:
            self.log_text.config(state=tk.NORMAL)
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{ts}] {msg}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.update_idletasks()
        except Exception as e:
            print(f"Logging error: {e}")
            print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def toggle_fullscreen(self, event=None):
        try:
            self.fullscreen = not self.fullscreen
            self.attributes("-fullscreen", self.fullscreen)
        except Exception as e:
            print(f"Fullscreen toggle error: {e}")
            try:
                if self.state() == "zoomed":
                    self.state("normal")
                else:
                    self.state("zoomed")
            except Exception:
                pass

    def on_closing(self):
        try:
            if self.is_processing:
                if messagebox.askyesno("Exit Confirmation", "A process is running. Are you sure you want to exit?"):
                    self.cancel_event.set()
                    self.destroy()
            else:
                if messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit?"):
                    self.destroy()
        except Exception as e:
            print(f"Closing error: {e}")
            self.destroy()

    def browse_folder(self):
        try:
            folder = filedialog.askdirectory(title="Select Folder")
            if folder:
                self.selected_folder.set(folder)
                self.safe_log_message(f"Selected folder: {folder}")
                self.selected_files = []
                if hasattr(self, "files_label"):
                    self.files_label.config(text="No files selected")
        except Exception as e:
            print(f"Folder browse error: {e}")

    def browse_files(self):
        try:
            files = filedialog.askopenfilenames(title="Select PDFs", filetypes=[("PDF Files", "*.pdf")])
            if files:
                self.selected_files = list(files)
                if hasattr(self, "files_label"):
                    self.files_label.config(text=f"{len(files)} file(s) selected")
                self.safe_log_message(f"Selected {len(files)} PDF files")
                self.selected_folder.set("")
        except Exception as e:
            print(f"Files browse error: {e}")

    def browse_output(self):
        try:
            file = filedialog.asksaveasfilename(
                title="Save As",
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialfile="kb_import.xlsx",
            )
            if file:
                self.output_path.set(file)
                self.safe_log_message(f"Output set to: {file}")
        except Exception as e:
            print(f"Output browse error: {e}")

    def browse_template(self):
        try:
            file = filedialog.askopenfilename(title="Select Template", filetypes=[("Excel", "*.xlsx")])
            if file:
                self.selected_template.set(file)
                self.safe_log_message(f"Template set to: {file}")
        except Exception as e:
            print(f"Template browse error: {e}")

    def clear_selection(self):
        self.selected_folder.set("")
        self.selected_files = []
        self.selected_template.set("")
        if hasattr(self, "files_label"):
            self.files_label.config(text="No files selected")
        self.progress_frame.reset()
        self.preview_btn.config(state=tk.DISABLED)
        self.safe_log_message("Selections cleared.")

    def view_logs(self):
        try:
            log_file = LOG_DIR / "app.log"
            if log_file.exists():
                open_file(log_file)
            else:
                messagebox.showinfo("Logs", "No log file found.")
        except Exception as e:
            print(f"Log view error: {e}")

    def preview_result(self):
        try:
            if self.result_file and Path(self.result_file).exists():
                open_file(self.result_file)
            else:
                messagebox.showinfo("Result", "No result file to preview.")
        except Exception as e:
            print(f"Preview error: {e}")

    def cancel_processing(self):
        if self.is_processing:
            self.cancel_event.set()
            self.status_text.set("Cancelling...")

    def process(self):
        if self.is_processing:
            return
        self.is_processing = True
        self.cancel_event.clear()
        self.process_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)
        self.status_text.set("Processing...")
        excel_path = self.output_path.get()
        template_path = self.selected_template.get() or None

        def progress_cb(msg):
            try:
                if hasattr(self, "progress_frame"):
                    current = self.progress_frame.processed_files.get() + 1
                    total = self.progress_frame.total_files.get()
                    self.after(0, lambda: self.progress_frame.update_progress(current, total, msg))
            except Exception:
                pass

        def ocr_cb(is_active):
            try:
                if hasattr(self, "progress_frame"):
                    self.after(0, lambda: self.progress_frame.set_ocr_active(is_active))
            except Exception:
                pass

        if self.selected_folder.get():
            folder = self.selected_folder.get()
            try:
                file_count = sum(1 for f in os.listdir(folder) if f.lower().endswith((".pdf", ".zip")))
                if hasattr(self, "progress_frame"):
                    self.after(0, lambda: self.progress_frame.show(file_count))
            except Exception:
                file_count = 0
            self.result_file, review_files, fail_count = process_files(
                folder,
                excel_path,
                template_path,
                progress_cb,
                ocr_cb,
                self.cancel_event,
            )
        elif self.selected_files:
            file_count = len(self.selected_files)
            if hasattr(self, "progress_frame"):
                self.after(0, lambda: self.progress_frame.show(file_count))
            self.result_file, review_files, fail_count = process_pdf_list(
                self.selected_files,
                excel_path,
                template_path,
                progress_cb,
                ocr_cb,
                self.cancel_event,
            )
        if self.cancel_event.is_set():
            self.after(0, lambda: self.safe_log_message("Process cancelled by user.", "warning"))
            return
        success_count = file_count - len(review_files) - fail_count
        if hasattr(self, "progress_frame"):
            self.after(0, lambda: self.progress_frame.update_final_status(success_count, len(review_files), fail_count))
        if self.result_file and Path(self.result_file).exists():
            self.after(0, lambda: self.safe_log_message("✓ Processing complete!", "success"))
            self.after(0, lambda: self.preview_btn.config(state=tk.NORMAL))
            summary = f"Total: {file_count} | Success: {success_count} | Review: {len(review_files)} | Failed: {fail_count}"
            create_success_log(summary)
            self.after(0, lambda: messagebox.showinfo("Processing Complete", f"Results:\n{summary}\n\nOutput: {self.result_file}"))
        else:
            self.after(0, lambda: self.safe_log_message("Processing failed or cancelled.", "error"))
            self.after(0, lambda: messagebox.showerror("Processing Failed", "No output file was created."))
        self.after(0, self._reset_ui_after_processing)

    def _reset_ui_after_processing(self):
        try:
            self.is_processing = False
            self.process_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.NORMAL)
            self.status_text.set("Ready.")
        except Exception as e:
            print(f"UI reset error: {e}")


def create_splash_screen():
    try:
        splash = tk.Tk()
        splash.overrideredirect(True)
        try:
            grad_frame = SafeGradientFrame(splash, BRAND_COLORS["secondary_purple"], BRAND_COLORS["header_bg"])
            grad_frame.pack(fill="both", expand=True)
        except Exception:
            grad_frame = tk.Frame(splash, bg=BRAND_COLORS["header_bg"])
            grad_frame.pack(fill="both", expand=True)
        splash.geometry("450x300")
        x = (splash.winfo_screenwidth() - 450) // 2
        y = (splash.winfo_screenheight() - 300) // 2
        splash.geometry(f"450x300+{x}+{y}")
        content_frame = tk.Frame(grad_frame, bg=grad_frame.cget("bg"))
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(content_frame, text="KYOCERA", font=("Arial Black", 28, "bold"), bg=grad_frame.cget("bg"), fg=BRAND_COLORS["kyocera_red"]).pack(pady=(10, 0))
        tk.Label(content_frame, text="QA ServiceNow Knowledge Tool", font=("Helvetica", 12), bg=grad_frame.cget("bg"), fg=BRAND_COLORS["header_fg"]).pack()
        try:
            spinner = SafeColorSpinnerCanvas(content_frame, width=80, height=80, bg=grad_frame.cget("bg"))
            spinner.pack(pady=20)
        except Exception:
            spinner = tk.Label(content_frame, text="Loading...", bg=grad_frame.cget("bg"), fg=BRAND_COLORS["header_fg"])
            spinner.pack(pady=20)
        status_var = tk.StringVar(value="Initializing...")
        tk.Label(content_frame, textvariable=status_var, font=("Helvetica", 10), bg=grad_frame.cget("bg"), fg=BRAND_COLORS["header_fg"]).pack(pady=(0, 10))
        return splash, status_var, spinner
    except Exception as e:
        print(f"Splash screen error: {e}")
        return None, None, None


def launch_app_with_splash():
    splash, status_var, spinner = create_splash_screen()
    if not splash:
        app = KyoQAToolApp()
        app.mainloop()
        return
    if hasattr(spinner, "start"):
        spinner.start()

    def initialize_and_launch():
        try:
            steps = [
                ("Loading modules...", 0.8),
                ("Checking environment...", 0.8),
                ("Starting application...", 1),
            ]
            for msg, delay in steps:
                if status_var:
                    status_var.set(msg)
                splash.update()
                time.sleep(delay)
            if hasattr(spinner, "stop"):
                spinner.stop()
            splash.destroy()
            app = KyoQAToolApp()
            app.mainloop()
        except Exception as e:
            log_exception(logger, "Application startup failed")
            try:
                messagebox.showerror("Startup Error", f"Critical error: {e}")
            finally:
                if splash and splash.winfo_exists():
                    splash.destroy()
                sys.exit(1)

    splash.after(100, initialize_and_launch)
    splash.mainloop()


if __name__ == "__main__":
    launch_app_with_splash()
