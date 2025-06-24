"""Reusable UI widgets for the KYO QA Tool."""

import tkinter as tk
from tkinter import ttk

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
            super().__init__(parent, **kwargs)
            self._color1, self._color2 = color1, color2
            self.bind("<Configure>", self._draw_gradient)
            self._gradient_drawn = False
        except Exception as e:
            print(f"GradientFrame init error: {e}")
            super().__init__(parent, bg=color1, **kwargs)

    def _draw_gradient(self, event=None):
        try:
            self.delete("gradient")
            w, h = self.winfo_width(), self.winfo_height()
            if w <= 1 or h <= 1:
                self.after(100, self._draw_gradient)
                return
            r1, g1, b1 = self.winfo_rgb(self._color1)
            r2, g2, b2 = self.winfo_rgb(self._color2)
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
            except Exception:
                pass
            self._after_id = None

    def _animate(self):
        if not self._is_spinning:
            return
        try:
            self.delete("all")
            w, h = self.winfo_width(), self.winfo_height()
            if w <= 10 or h <= 10:
                self._after_id = self.after(50, self._animate)
                return
            cx, cy, r = w / 2, h / 2, min(w, h) / 2 - 5
            if r <= 0:
                self._after_id = self.after(50, self._animate)
                return
            for i in range(5):
                start = self._angle + (i * 72)
                color = self._spinner_colors[(self._color_index + i) % 5]
                self.create_arc(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    start=start,
                    extent=45,
                    style=tk.ARC,
                    outline=color,
                    width=4,
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
            self.progress = ttk.Progressbar(
                self, orient=tk.HORIZONTAL, length=400, mode="determinate"
            )
            self.progress.grid(row=0, column=0, columnspan=5, pady=(0, 10), sticky="ew")
            labels = ["Total:", "Processed:", "Success:", "Needs Review:", "Failed:"]
            for i, label in enumerate(labels):
                ttk.Label(self, text=label, font=("Helvetica", 10, "bold")).grid(
                    row=1, column=i, padx=10, sticky="s"
                )
            vars_and_colors = [
                (self.total_files, "black"),
                (self.processed_files, "black"),
                (self.successful_files, BRAND_COLORS["success"]),
                (self.review_files, BRAND_COLORS["warning"]),
                (self.failed_files, BRAND_COLORS["error"]),
            ]
            for i, (var, _color) in enumerate(vars_and_colors):
                label = ttk.Label(self, textvariable=var, font=("Helvetica", 12, "bold"))
                label.grid(row=2, column=i, padx=10, sticky="n")
            status_frame = ttk.Frame(self)
            status_frame.grid(row=3, column=0, columnspan=5, pady=(10, 0), sticky="w")
            self.status_text = tk.StringVar()
            self.status_label = ttk.Label(status_frame, textvariable=self.status_text)
            self.status_label.pack(side=tk.LEFT)
            self.ocr_label = ttk.Label(
                status_frame, text="(OCR Active)", foreground=BRAND_COLORS["warning"]
            )
            for i in range(5):
                self.columnconfigure(i, weight=1)
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
            for var in [
                self.total_files,
                self.processed_files,
                self.successful_files,
                self.review_files,
                self.failed_files,
            ]:
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
