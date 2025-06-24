# KYO QA ServiceNow Tool - Clean, Bug-Resistant Version
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
    from file_utils import ensure_folders, cleanup_temp_files, open_file
    from logging_utils import (
        setup_logger,
        create_success_log,
        create_failure_log,
        LOG_DIR,
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not found: {e}")
    MODULES_AVAILABLE = False
    
    # Mock functions for testing
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

# Official Kyocera Brand Colors
BRAND_COLORS = {
    "primary_dark_grey": "#282828",
    "primary_light_grey": "#F2F2F2",
    "secondary_purple": "#6E3CBE",
    "secondary_blue": "#0A9BCD",
    "secondary_yellow": "#F5B400",
    "secondary_orange": "#F06400",
    "kyocera_red": "#E30613",
    "csr_green": "#00B176",
    "background": "#F2F2F2",
    "text": "#282828",
    "header_bg": "#282828",
    "header_fg": "#F2F2F2",
    "success": "#00B176",
    "warning": "#F5B400",
    "error": "#E30613",
    "info": "#0A9BCD",
    "button": "#0A9BCD",
    "button_hover": "#6E3CBE",
    "cancel_button": "#f39c12",
    "cancel_button_hover": "#e67e22",
    "button_text": "#F2F2F2",
}

class SafeGradientFrame(tk.Canvas):
    """A canvas with a vertical gradient background - with error handling."""

    def __init__(self, parent, color1, color2, **kwargs):
        try:
            tk.Canvas.__init__(self, parent, **kwargs)
            self._color1, self._color2 = color1, color2
            self.bind("<Configure>", self._draw_gradient)
            self._gradient_drawn = False
        except Exception as e:
            print(f"GradientFrame init error: {e}")
            # Fallback to regular canvas
            tk.Canvas.__init__(self, parent, bg=color1, **kwargs)

    def _draw_gradient(self, event=None):
        try:
            self.delete("gradient")
            w, h = self.winfo_width(), self.winfo_height()
            
            # Prevent errors with invalid dimensions
            if w <= 1 or h <= 1:
                self.after(100, self._draw_gradient)  # Retry later
                return
            
            (r1, g1, b1) = self.winfo_rgb(self._color1)
            (r2, g2, b2) = self.winfo_rgb(self._color2)
            
            # Prevent division by zero
            if h == 0:
                return
                
            r, g, b = float(r2 - r1) / h, float(g2 - g1) / h, float(b2 - b1) / h
            
            for i in range(h):
                nr, ng, nb = int(r1 + (r * i)), int(g1 + (g * i)), int(b1 + (b * i))
                color = f"#{nr:04x}{ng:04x}{nb:04x}"
                self.create_line(0, i, w, i, tags=("gradient",), fill=color)
            
            self._gradient_drawn = True
            
        except Exception as e:
            print(f"Gradient drawing error: {e}")
            # Fallback to solid color
            self.configure(bg=self._color1)

class SafeColorSpinnerCanvas(tk.Canvas):
    """Color spinner with robust error handling."""
    
    def __init__(self, parent, **kwargs):
        try:
            super().__init__(parent, **kwargs)
            self.configure(highlightthickness=0)
            self._is_spinning = False
            self._angle = 0
            self._color_index = 0
            self._spinner_colors = [
                BRAND_COLORS["secondary_blue"],
                BRAND_COLORS["secondary_purple"],
                BRAND_COLORS["secondary_orange"],
                BRAND_COLORS["secondary_yellow"],
                BRAND_COLORS["csr_green"],
            ]
            self._after_id = None
        except Exception as e:
            print(f"ColorSpinner init error: {e}")
            super().__init__(parent, **kwargs)

    def start(self):
        try:
            self._is_spinning = True
            self._animate()
        except Exception as e:
            print(f"Spinner start error: {e}")

    def stop(self):
        self._is_spinning = False
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except:
                pass
            self._after_id = None

    def _animate(self):
        if not self._is_spinning:
            return
        
        try:
            self.delete("all")
            w, h = self.winfo_width(), self.winfo_height()
            
            # Prevent errors with invalid dimensions
            if w <= 10 or h <= 10:
                self._after_id = self.after(50, self._animate)
                return
                
            cx, cy, r = w / 2, h / 2, min(w, h) / 2 - 5
            
            # Prevent negative radius
            if r <= 0:
                self._after_id = self.after(50, self._animate)
                return
                
            for i in range(5):
                start = self._angle + (i * 72)
                color = self._spinner_colors[(self._color_index + i) % 5]
                self.create_arc(
                    cx - r, cy - r, cx + r, cy + r,
                    start=start, extent=45, style=tk.ARC,
                    outline=color, width=4,
                )
            
            self._angle = (self._angle - 15) % 360
            if self._angle % 90 == 0:
                self._color_index = (self._color_index + 1) % 5
            
            self._after_id = self.after(50, self._animate)
            
        except Exception as e:
            print(f"Animation error: {e}")
            self._is_spinning = False

class SafeProgressFrame(ttk.Frame):
    """Progress frame with error handling."""
    
    def __init__(self, parent):
        try:
            super().__init__(parent, padding="10")
            self._setup_variables()
            self._create_widgets()
        except Exception as e:
            print(f"ProgressFrame init error: {e}")
            super().__init__(parent)

    def _setup_variables(self):
        self.total_files = tk.IntVar(value=0)
        self.processed_files = tk.IntVar(value=0)
        self.successful_files = tk.IntVar(value=0)
        self.review_files = tk.IntVar(value=0)
        self.failed_files = tk.IntVar(value=0)

    def _create_widgets(self):
        try:
            # Progress bar
            self.progress = ttk.Progressbar(
                self, orient=tk.HORIZONTAL, length=400, mode="determinate"
            )
            self.progress.grid(row=0, column=0, columnspan=5, pady=(0, 10), sticky="ew")
            
            # Labels
            labels = ["Total:", "Processed:", "Success:", "Needs Review:", "Failed:"]
            for i, label in enumerate(labels):
                ttk.Label(self, text=label, font=("Helvetica", 10, "bold")).grid(
                    row=1, column=i, padx=10, sticky="s"
                )
            
            # Values
            vars_and_colors = [
                (self.total_files, "black"),
                (self.processed_files, "black"), 
                (self.successful_files, BRAND_COLORS["success"]),
                (self.review_files, BRAND_COLORS["warning"]),
                (self.failed_files, BRAND_COLORS["error"]),
            ]
            
            for i, (var, color) in enumerate(vars_and_colors):
                label = ttk.Label(self, textvariable=var, font=("Helvetica", 12, "bold"))
                label.grid(row=2, column=i, padx=10, sticky="n")
            
            # Status
            status_frame = ttk.Frame(self)
            status_frame.grid(row=3, column=0, columnspan=5, pady=(10, 0), sticky="w")
            
            self.status_text = tk.StringVar()
            self.status_label = ttk.Label(status_frame, textvariable=self.status_text)
            self.status_label.pack(side=tk.LEFT)
            
            self.ocr_label = ttk.Label(status_frame, text="(OCR Active)", foreground=BRAND_COLORS["warning"])
            
            # Configure grid weights
            for i in range(5):
                self.columnconfigure(i, weight=1)
            
            # Initially hidden
            self.grid_remove()
            
        except Exception as e:
            print(f"ProgressFrame widget creation error: {e}")

    def set_ocr_active(self, is_active):
        try:
            if is_active:
                self.ocr_label.pack(side=tk.LEFT, padx=(5, 0))
            else:
                self.ocr_label.pack_forget()
        except Exception as e:
            print(f"OCR status update error: {e}")

    def reset(self):
        try:
            for var in [self.total_files, self.processed_files, self.successful_files, 
                       self.review_files, self.failed_files]:
                var.set(0)
            self.progress["value"] = 0
            self.status_text.set("")
        except Exception as e:
            print(f"Progress reset error: {e}")

    def update_progress(self, current, total, status=""):
        try:
            self.processed_files.set(current)
            self.status_text.set(status)
            if total > 0:
                self.progress["value"] = (current / total) * 100
        except Exception as e:
            print(f"Progress update error: {e}")

    def update_final_status(self, success, review, failed):
        try:
            self.successful_files.set(success)
            self.review_files.set(review)
            self.failed_files.set(failed)
        except Exception as e:
            print(f"Final status update error: {e}")

    def show(self, total):
        try:
            self.reset()
            self.total_files.set(total)
            self.grid()
        except Exception as e:
            print(f"Progress show error: {e}")

class KyoQAToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Initialize variables first
        self.is_processing = False
        self.cancel_event = threading.Event()
        self.fullscreen = False
        self.result_file = None
        
        # Setup basic window
        self._setup_window()
        
        # Initialize tkinter variables
        self._setup_variables()
        
        # Setup GUI
        try:
            self.setup_styles()
            self.create_widgets()
        except Exception as e:
            print(f"GUI setup error: {e}")
            self._create_fallback_gui()
        
        # Initialize
        self._initialize_app()

    def _setup_window(self):
        """Setup basic window properties."""
        try:
            self.title(f"Kyocera QA ServiceNow Knowledge Tool {VERSION}")
            self.configure(bg=BRAND_COLORS["background"])
            
            # Try fullscreen, fallback to maximized
            try:
                self.attributes("-fullscreen", True)
                self.fullscreen = True
            except:
                self.state('zoomed')
                self.fullscreen = False
            
            # Try to load icon
            try:
                base_path = getattr(sys, "_MEIPASS", Path(__file__).parent)
                icon_path = base_path / "kyo_icon.ico"
                if icon_path.exists():
                    self.iconbitmap(icon_path)
            except:
                pass  # Continue without icon
                
        except Exception as e:
            print(f"Window setup error: {e}")
            self.geometry("900x700")

    def _setup_variables(self):
        """Initialize tkinter variables."""
        try:
            self.selected_folder = tk.StringVar()
            self.selected_files = []
            self.selected_template = tk.StringVar()
            self.status_text = tk.StringVar(value="Ready to process files.")
            self.output_path = tk.StringVar(
                value=str(Path.cwd() / "output" / "kb_import_file.xlsx")
            )
        except Exception as e:
            print(f"Variable setup error: {e}")

    def setup_styles(self):
        """Setup TTK styles with error handling."""
        try:
            self.style = ttk.Style(self)
            self.style.theme_use("clam")
            
            # Basic styles that are most likely to work
            self.style.configure("TLabel", 
                               background=BRAND_COLORS["background"],
                               foreground=BRAND_COLORS["text"])
            
            self.style.configure("TFrame", 
                               background=BRAND_COLORS["background"])
                               
            self.style.configure("TButton",
                               background=BRAND_COLORS["button"],
                               foreground=BRAND_COLORS["button_text"])
            
            # More complex styles
            try:
                self.style.configure("Header.TFrame", 
                                   background=BRAND_COLORS["header_bg"])
                
                self.style.configure("Header.TLabel",
                                   background=BRAND_COLORS["header_bg"],
                                   foreground=BRAND_COLORS["header_fg"],
                                   font=("Helvetica", 16, "bold"))
                
                self.style.configure("KyoceraLogo.TLabel",
                                   background=BRAND_COLORS["header_bg"],
                                   foreground=BRAND_COLORS["kyocera_red"],
                                   font=("Arial Black", 20, "bold"))
            except Exception as e:
                print(f"Advanced style setup error: {e}")
                
        except Exception as e:
            print(f"Style setup error: {e}")

    def create_widgets(self):
        """Create the main GUI widgets."""
        try:
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            
            # Header
            self._create_header()
            
            # Main content
            self._create_main_content()
            
            # Status bar
            self._create_status_bar()
            
        except Exception as e:
            print(f"Widget creation error: {e}")
            raise

    def _create_header(self):
        """Create header section."""
        try:
            header_frame = ttk.Frame(self, style="Header.TFrame", padding=(10, 5))
            header_frame.grid(row=0, column=0, sticky="ew")
            
            ttk.Label(header_frame, text="KYOCERA", style="KyoceraLogo.TLabel").pack(
                side=tk.LEFT, padx=(5, 0)
            )
            ttk.Label(header_frame, text="QA ServiceNow Knowledge Tool", 
                     style="Header.TLabel").pack(side=tk.LEFT, padx=(10, 0))
            ttk.Label(header_frame, text=f"v{VERSION}",
                     background=BRAND_COLORS["header_bg"],
                     foreground=BRAND_COLORS["header_fg"]).pack(side=tk.RIGHT, padx=10)
        except Exception as e:
            print(f"Header creation error: {e}")

    def _create_main_content(self):
        """Create main content area."""
        try:
            main_frame = ttk.Frame(self, padding=10)
            main_frame.grid(row=1, column=0, sticky="nsew")
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(3, weight=1)
            
            # Input/Output section
            self._create_io_section(main_frame)
            
            # Process section
            self._create_process_section(main_frame)
            
            # Progress section
            self.progress_frame = SafeProgressFrame(main_frame)
            self.progress_frame.grid(row=2, column=0, sticky="ew", pady=5)
            
            # Log section
            self._create_log_section(main_frame)
            
        except Exception as e:
            print(f"Main content creation error: {e}")

    def _create_io_section(self, parent):
        """Create input/output section."""
        try:
            io_frame = ttk.LabelFrame(parent, text="1. Select Inputs & Outputs", padding=10)
            io_frame.grid(row=0, column=0, sticky="ew", pady=5)
            io_frame.columnconfigure(1, weight=1)
            
            # Folder selection
            ttk.Label(io_frame, text="Process Folder:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
            ttk.Entry(io_frame, textvariable=self.selected_folder).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            ttk.Button(io_frame, text="📂 Browse...", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)
            
            # File selection
            ttk.Label(io_frame, text="Or Select PDFs:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
            self.files_label = ttk.Label(io_frame, text="No files selected", wraplength=400)
            self.files_label.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
            ttk.Button(io_frame, text="📄 Select...", command=self.browse_files).grid(row=1, column=2, padx=5, pady=5)
            
            # Output path
            ttk.Label(io_frame, text="Excel Output:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
            ttk.Entry(io_frame, textvariable=self.output_path).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
            ttk.Button(io_frame, text="💾 Browse...", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)
            
            # Template
            ttk.Label(io_frame, text="Template (optional):").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
            ttk.Entry(io_frame, textvariable=self.selected_template).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
            ttk.Button(io_frame, text="📋 Browse...", command=self.browse_template).grid(row=3, column=2, padx=5, pady=5)
            
        except Exception as e:
            print(f"IO section creation error: {e}")

    def _create_process_section(self, parent):
        """Create process control section."""
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
        """Create log display section."""
        try:
            log_frame = ttk.LabelFrame(parent, text="Activity Log", padding=10)
            log_frame.grid(row=3, column=0, sticky="nsew", pady=5)
            log_frame.rowconfigure(0, weight=1)
            log_frame.columnconfigure(0, weight=1)
            
            # Text widget with scrollbar
            text_frame = ttk.Frame(log_frame)
            text_frame.grid(row=0, column=0, sticky="nsew")
            text_frame.rowconfigure(0, weight=1)
            text_frame.columnconfigure(0, weight=1)
            
            self.log_text = tk.Text(text_frame, height=10, width=80, wrap=tk.WORD,
                                   bg="white", fg=BRAND_COLORS["text"], state=tk.DISABLED)
            self.log_text.grid(row=0, column=0, sticky="nsew")
            
            scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.log_text.config(yscrollcommand=scrollbar.set)
            
            # Configure text tags for colors
            try:
                self.log_text.tag_configure("success", foreground=BRAND_COLORS["success"])
                self.log_text.tag_configure("warning", foreground=BRAND_COLORS["warning"])
                self.log_text.tag_configure("error", foreground=BRAND_COLORS["error"])
                self.log_text.tag_configure("info", foreground=BRAND_COLORS["info"])
            except:
                pass  # Continue without colored tags
                
        except Exception as e:
            print(f"Log section creation error: {e}")

    def _create_status_bar(self):
        """Create status bar."""
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
        """Create a simple fallback GUI if main creation fails."""
        try:
            # Clear any existing widgets
            for widget in self.winfo_children():
                widget.destroy()
            
            # Simple layout
            main_label = tk.Label(self, text=f"KYO QA Tool v{VERSION}", 
                                 font=("Helvetica", 16), bg=BRAND_COLORS["background"])
            main_label.pack(pady=20)
            
            error_label = tk.Label(self, text="GUI Error - Using Fallback Mode", 
                                  fg="red", bg=BRAND_COLORS["background"])
            error_label.pack(pady=10)
            
            # Basic buttons
            tk.Button(self, text="Select Folder", command=self.browse_folder).pack(pady=5)
            tk.Button(self, text="Process", command=self.process).pack(pady=5)
            tk.Button(self, text="Exit", command=self.on_closing).pack(pady=5)
            
        except Exception as e:
            print(f"Fallback GUI creation error: {e}")

    def _initialize_app(self):
        """Initialize the application."""
        try:
            # Setup key bindings
            self.bind("<Escape>", self.toggle_fullscreen)
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Initialize folders and cleanup
            ensure_folders()
            cleanup_temp_files()
            
            # Log startup
            self.safe_log_message(f"Kyocera QA Tool v{VERSION} Initialized", "info")
            self.safe_log_message("Please select a folder or PDF files to begin.")
            
        except Exception as e:
            print(f"App initialization error: {e}")

    # Safe logging method
    def safe_log_message(self, msg, tag=None):
        """Log message with error handling."""
        try:
            self.log_text.config(state=tk.NORMAL)
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{ts}] {msg}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.update_idletasks()
        except Exception as e:
            print(f"Logging error: {e}")
            # Fallback to console
            print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    # Event handlers with error handling
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode safely."""
        try:
            self.fullscreen = not self.fullscreen
            self.attributes("-fullscreen", self.fullscreen)
        except Exception as e:
            print(f"Fullscreen toggle error: {e}")
            try:
                if self.state() == 'zoomed':
                    self.state('normal')
                else:
                    self.state('zoomed')
            except:
                pass

    def on_closing(self):
        """Handle window closing."""
        try:
            if self.is_processing:
                if messagebox.askyesno("Exit Confirmation", 
                    "A process is running. Are you sure you want to exit?"):
                    self.cancel_event.set()
                    self.destroy()
            else:
                if messagebox.askyesno("Exit Confirmation", 
                    "Are you sure you want to exit?"):
                    self.destroy()
        except Exception as e:
            print(f"Closing error: {e}")
            self.destroy()

    # File browser methods
    def browse_folder(self):
        """Browse for folder."""
        try:
            folder = filedialog.askdirectory(title="Select Folder")
            if folder:
                self.selected_folder.set(folder)
                self.safe_log_message(f"Selected folder: {folder}")
                self.selected_files = []
                if hasattr(self, 'files_label'):
                    self.files_label.config(text="No files selected")
        except Exception as e:
            print(f"Folder browse error: {e}")

    def browse_files(self):
        """Browse for individual files."""
        try:
            files = filedialog.askopenfilenames(title="Select PDFs", 
                                              filetypes=[("PDF Files", "*.pdf")])
            if files:
                self.selected_files = list(files)
                if hasattr(self, 'files_label'):
                    self.files_label.config(text=f"{len(files)} file(s) selected")
                self.safe_log_message(f"Selected {len(files)} PDF files")
                self.selected_folder.set("")
        except Exception as e:
            print(f"Files browse error: {e}")

    def browse_output(self):
        """Browse for output file."""
        try:
            file = filedialog.asksaveasfilename(title="Save As", 
                                              defaultextension=".xlsx",
                                              filetypes=[("Excel", "*.xlsx")],
                                              initialfile="kb_import.xlsx")
            if file:
                self.output_path.set(file)
                self.safe_log_message(f"Output set to: {file}")
        except Exception as e:
            print(f"Output browse error: {e}")

    def browse_template(self):
        """Browse for template file."""
        try:
            file = filedialog.askopenfilename(title="Select Template", 
                                            filetypes=[("Excel", "*.xlsx")])
            if file:
                self.selected_template.set(file)
                self.safe_log_message(f"Template set to: {file}")
        except Exception as e:
            print(f"Template browse error: {e}")

    def view_logs(self):
        """Open logs folder."""
        try:
            if open_file(LOG_DIR):
                self.safe_log_message(f"Opening logs folder: {LOG_DIR}")
            else:
                self.safe_log_message("Could not open logs folder", "error")
        except Exception as e:
            self.safe_log_message(f"Logs error: {e}", "error")

    def clear_selection(self):
        """Clear all selections."""
        try:
            self.selected_folder.set("")
            self.selected_files = []
            self.selected_template.set("")
            if hasattr(self, 'files_label'):
                self.files_label.config(text="No files selected")
            self.safe_log_message("Selections cleared.")
            self.preview_btn.config(state=tk.DISABLED)
            self.result_file = None
            if hasattr(self, 'progress_frame'):
                self.progress_frame.grid_remove()
        except Exception as e:
            print(f"Clear selection error: {e}")

    def preview_result(self):
        """Preview result file."""
        try:
            if self.result_file and Path(self.result_file).exists():
                if open_file(self.result_file):
                    self.safe_log_message(f"Opening result file: {self.result_file}")
                else:
                    messagebox.showinfo("Open Manually", 
                        f"Could not open automatically.\nFile location:\n{self.result_file}")
            else:
                messagebox.showwarning("File Not Found", "Result file not found.")
        except Exception as e:
            self.safe_log_message(f"Preview error: {e}", "error")

    # Processing methods
    def process(self):
        """Start processing."""
        try:
            if not self.selected_folder.get() and not self.selected_files:
                messagebox.showwarning("Input Missing", "Please select a folder or PDF files.")
                return
            
            self.is_processing = True
            self.cancel_event.clear()
            
            # Update UI
            self.process_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.DISABLED)
            self.status_text.set("Processing...")
            
            if hasattr(self, 'progress_frame'):
                self.progress_frame.show(1)
            
            # Start processing thread
            threading.Thread(target=self._process_worker, daemon=True).start()
            
        except Exception as e:
            self.safe_log_message(f"Process start error: {e}", "error")

    def cancel_processing(self):
        """Cancel processing."""
        try:
            self.status_text.set("Cancellation requested...")
            self.cancel_event.set()
            self.cancel_btn.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Cancel error: {e}")

    def _process_worker(self):
        """Main processing worker thread."""
        try:
            excel_path = self.output_path.get()
            template_path = self.selected_template.get() or None
            
            # Ensure output directory exists
            Path(excel_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.safe_log_message("--- Starting Process ---", "info")
            
            def progress_cb(msg):
                try:
                    self.after(0, lambda: self.safe_log_message(msg))
                    # Update progress if possible
                    match = re.search(r"(\d+)/(\d+)", msg)
                    if match and hasattr(self, 'progress_frame'):
                        current, total = int(match.group(1)), int(match.group(2))
                        self.after(0, lambda: self.progress_frame.update_progress(current, total, msg))
                except:
                    pass

            def ocr_cb(is_active):
                try:
                    if hasattr(self, 'progress_frame'):
                        self.after(0, lambda: self.progress_frame.set_ocr_active(is_active))
                except:
                    pass

            # Process files
            if self.selected_folder.get():
                folder = self.selected_folder.get()
                try:
                    file_count = sum(1 for f in os.listdir(folder) 
                                   if f.lower().endswith((".pdf", ".zip")))
                    if hasattr(self, 'progress_frame'):
                        self.after(0, lambda: self.progress_frame.show(file_count))
                except:
                    file_count = 0
                
                self.result_file, review_files, fail_count = process_files(
                    folder, excel_path, template_path, progress_cb, ocr_cb, self.cancel_event
                )
            elif self.selected_files:
                file_count = len(self.selected_files)
                if hasattr(self, 'progress_frame'):
                    self.after(0, lambda: self.progress_frame.show(file_count))
                
                self.result_file, review_files, fail_count = process_pdf_list(
                    self.selected_files, excel_path, template_path, progress_cb, ocr_cb, self.cancel_event
                )

            # Handle results
            if self.cancel_event.is_set():
                self.after(0, lambda: self.safe_log_message("Process cancelled by user.", "warning"))
                return

            success_count = file_count - len(review_files) - fail_count
            if hasattr(self, 'progress_frame'):
                self.after(0, lambda: self.progress_frame.update_final_status(
                    success_count, len(review_files), fail_count))

            if self.result_file and Path(self.result_file).exists():
                self.after(0, lambda: self.safe_log_message("✓ Processing complete!", "success"))
                self.after(0, lambda: self.preview_btn.config(state=tk.NORMAL))
                
                summary = f"Total: {file_count} | Success: {success_count} | Review: {len(review_files)} | Failed: {fail_count}"
                create_success_log(summary)
                
                self.after(0, lambda: messagebox.showinfo("Processing Complete", 
                    f"Results:\n{summary}\n\nOutput: {self.result_file}"))
            else:
                self.after(0, lambda: self.safe_log_message("Processing failed or cancelled.", "error"))
                self.after(0, lambda: messagebox.showerror("Processing Failed", "No output file was created."))

        except Exception as e:
            logger.exception(f"Processing error: {e}")
            self.after(0, lambda: self.safe_log_message(f"CRITICAL ERROR: {e}", "error"))
            create_failure_log("Critical processing failure", str(e))
            self.after(0, lambda: messagebox.showerror("Critical Error", f"Error: {e}"))
        
        finally:
            # Reset UI state
            self.after(0, self._reset_ui_after_processing)

    def _reset_ui_after_processing(self):
        """Reset UI after processing completes."""
        try:
            self.is_processing = False
            self.process_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.NORMAL)
            self.status_text.set("Ready.")
        except Exception as e:
            print(f"UI reset error: {e}")

def create_splash_screen():
    """Create splash screen with error handling."""
    try:
        splash = tk.Tk()
        splash.overrideredirect(True)
        
        # Create gradient background
        try:
            grad_frame = SafeGradientFrame(splash, 
                BRAND_COLORS["secondary_purple"], BRAND_COLORS["header_bg"])
            grad_frame.pack(fill="both", expand=True)
        except:
            # Fallback to solid color
            grad_frame = tk.Frame(splash, bg=BRAND_COLORS["header_bg"])
            grad_frame.pack(fill="both", expand=True)
        
        # Position splash
        splash.geometry("450x300")
        x = (splash.winfo_screenwidth() - 450) // 2
        y = (splash.winfo_screenheight() - 300) // 2
        splash.geometry(f"450x300+{x}+{y}")
        
        # Content frame
        content_frame = tk.Frame(grad_frame, bg=grad_frame.cget("bg"))
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        tk.Label(content_frame, text="KYOCERA", font=("Arial Black", 28, "bold"),
                bg=grad_frame.cget("bg"), fg=BRAND_COLORS["kyocera_red"]).pack(pady=(10, 0))
        
        tk.Label(content_frame, text="QA ServiceNow Knowledge Tool", 
                font=("Helvetica", 12), bg=grad_frame.cget("bg"), 
                fg=BRAND_COLORS["header_fg"]).pack()
        
        # Spinner
        try:
            spinner = SafeColorSpinnerCanvas(content_frame, width=80, height=80, 
                                           bg=grad_frame.cget("bg"))
            spinner.pack(pady=20)
        except:
            # Fallback to simple label
            spinner = tk.Label(content_frame, text="Loading...", 
                             bg=grad_frame.cget("bg"), fg=BRAND_COLORS["header_fg"])
            spinner.pack(pady=20)
        
        # Status
        status_var = tk.StringVar(value="Initializing...")
        tk.Label(content_frame, textvariable=status_var, font=("Helvetica", 10),
                bg=grad_frame.cget("bg"), fg=BRAND_COLORS["header_fg"]).pack(pady=(0, 10))
        
        return splash, status_var, spinner
        
    except Exception as e:
        print(f"Splash screen error: {e}")
        return None, None, None

def launch_app_with_splash():
    """Launch app with splash screen."""
    splash, status_var, spinner = create_splash_screen()
    
    if not splash:
        # Direct launch if splash fails
        app = KyoQAToolApp()
        app.mainloop()
        return
    
    # Start spinner if available
    if hasattr(spinner, 'start'):
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
            
            # Stop spinner
            if hasattr(spinner, 'stop'):
                spinner.stop()
            
            splash.destroy()
            
            # Launch main app
            app = KyoQAToolApp()
            app.mainloop()
            
        except Exception as e:
            logger.exception("Application startup failed")
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