"""
app.py

PromptShape - Standalone AI CAD Code Generator for FreeCAD.

Required files in the same folder:
- app.py
- classifier.py
- generators.py

Features:
- Classic Windows look
- Starts Ollama automatically
- Shows loading popup while Ollama starts
- Stops Ollama when app closes, but only if this app started it
- AI detects the shape
- Generates FreeCAD Python code
- Runs generated macro in current or new FreeCAD window
"""

import os
import subprocess
import tempfile
import time
import threading
import urllib.request
import atexit
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from classifier import classify, SUPPORTED_TYPES
from generators import DEFAULT_PARAMS, generate_freecad_code, get_default_params


APP_TITLE = "PromptShape"
FREECAD_EXE = r"C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe"

OLLAMA_PROCESS = None
OLLAMA_STARTED_BY_APP = False


# =============================================================
# Ollama helpers
# =============================================================

def is_ollama_ready():
    try:
        with urllib.request.urlopen(
            "http://localhost:11434/api/tags",
            timeout=2,
        ):
            return True
    except Exception:
        return False


def start_ollama_server():
    global OLLAMA_PROCESS
    global OLLAMA_STARTED_BY_APP

    if is_ollama_ready():
        return True

    try:
        OLLAMA_PROCESS = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        OLLAMA_STARTED_BY_APP = True
        return True

    except Exception:
        return False


def stop_ollama_server():
    global OLLAMA_PROCESS
    global OLLAMA_STARTED_BY_APP

    if OLLAMA_STARTED_BY_APP and OLLAMA_PROCESS:
        try:
            OLLAMA_PROCESS.terminate()
            OLLAMA_PROCESS.wait(timeout=5)
        except Exception:
            try:
                OLLAMA_PROCESS.kill()
            except Exception:
                pass


atexit.register(stop_ollama_server)


# =============================================================
# Theme
# =============================================================

def apply_classic_theme(root):
    style = ttk.Style(root)

    try:
        style.theme_use("classic")
    except Exception:
        style.theme_use("clam")

    bg = "#d4d0c8"

    root.configure(bg=bg)

    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground="#000000")
    style.configure("TEntry", padding=2)
    style.configure("TCombobox", padding=2)

    style.configure(
        "Status.TLabel",
        background=bg,
        foreground="#000000",
        relief="sunken",
        padding=3,
    )

    return style


def make_classic_button(parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg="#d4d0c8",
        activebackground="#d4d0c8",
        foreground="#000000",
        activeforeground="#000000",
        relief="raised",
        bd=2,
        highlightthickness=0,
        padx=8,
        pady=2,
    )


def make_classic_menubutton(parent, text):
    return tk.Menubutton(
        parent,
        text=text,
        bg="#d4d0c8",
        activebackground="#d4d0c8",
        foreground="#000000",
        activeforeground="#000000",
        relief="raised",
        bd=2,
        highlightthickness=0,
        padx=8,
        pady=2,
    )


# =============================================================
# Main app
# =============================================================

class AICADCodeGeneratorApp(tk.Tk):
    def clear_code(self):
        self.prompt_entry.delete(0, tk.END)
        self.code_text.delete("1.0", tk.END)
        for child in self.params_frame.winfo_children():
            child.destroy()
        self.param_vars = {}
        self.current_shape = None
        self.status_var.set("Ready")
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        apply_classic_theme(self)

        self.geometry("1150x760")
        self.minsize(950, 620)

        self.shape_type_var = tk.StringVar(value="")
        self.param_vars = {}
        self.current_shape = "rectangle"
        self.ollama_ready_flag = False

        self.create_widgets()
        for child in self.params_frame.winfo_children():
            child.destroy()
        self.after(100, self.clear_code)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.after(200, self.show_ollama_loading_screen)

    # =========================================================
    # UI
    # =========================================================

    def create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top_frame = ttk.Frame(self, padding=10)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(
            top_frame,
            text="Prompt:"
        ).grid(row=0, column=0, sticky="w")

        self.prompt_entry = ttk.Entry(top_frame)
        self.prompt_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=8
        )
        self.prompt_entry.insert(0, "")

        make_classic_button(
            top_frame,
            "Detect Shape with AI",
            self.detect_shape,
        ).grid(row=0, column=2, padx=4)

        make_classic_button(
            top_frame,
            "Generate Code",
            self.generate_code,
        ).grid(row=0, column=3, padx=4)

        make_classic_button(
            top_frame,
            "Copy Code",
            self.copy_code,
        ).grid(row=0, column=4, padx=4)

        make_classic_button(
            top_frame,
            "Save .py",
            self.save_code,
        ).grid(row=0, column=5, padx=4)

        run_button = make_classic_menubutton(
            top_frame,
            "Run in FreeCAD"
        )

        run_menu = tk.Menu(
            run_button,
            tearoff=0,
            bg="#d4d0c8",
            activebackground="#0a246a",
            activeforeground="#ffffff",
        )

        run_menu.add_command(
            label="Open in Current FreeCAD Window",
            command=lambda: self.run_in_freecad(mode="current"),
        )

        run_menu.add_command(
            label="Open in New FreeCAD Window",
            command=lambda: self.run_in_freecad(mode="new"),
        )

        run_button["menu"] = run_menu
        run_button.grid(row=0, column=6, padx=4)

        main_pane = ttk.PanedWindow(
            self,
            orient=tk.HORIZONTAL
        )

        main_pane.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )

        left_frame = ttk.Frame(
            main_pane,
            padding=10
        )

        right_frame = ttk.Frame(
            main_pane,
            padding=10
        )

        main_pane.add(left_frame, weight=1)
        main_pane.add(right_frame, weight=3)

        self.build_left_panel(left_frame)
        self.build_right_panel(right_frame)

        self.status_var = tk.StringVar(value="Ready")

        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w",
        )

        status_bar.grid(
            row=2,
            column=0,
            sticky="ew"
        )

    # =========================================================
    # Left panel
    # =========================================================

    def build_left_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(
            parent,
            text="Parameters:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        param_outer = ttk.Frame(parent)
        param_outer.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        param_outer.columnconfigure(0, weight=1)
        param_outer.rowconfigure(0, weight=1)

        self.param_canvas = tk.Canvas(
            param_outer,
            highlightthickness=0,
            bg="#d4d0c8",
        )

        self.param_canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar = ttk.Scrollbar(
            param_outer,
            orient="vertical",
            command=self.param_canvas.yview,
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.param_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.params_frame = ttk.Frame(
            self.param_canvas
        )

        self.param_window = self.param_canvas.create_window(
            (0, 0),
            window=self.params_frame,
            anchor="nw",
        )

        self.params_frame.bind(
            "<Configure>",
            self.update_param_scroll_region
        )

        self.param_canvas.bind(
            "<Configure>",
            self.update_param_canvas_width
        )

    # =========================================================
    # Right panel
    # =========================================================

    def build_right_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(
            parent,
            text="Generated FreeCAD Python Code:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        code_frame = ttk.Frame(parent)

        code_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=(3, 0)
        )

        code_frame.columnconfigure(0, weight=1)
        code_frame.rowconfigure(0, weight=1)

        self.code_text = tk.Text(
            code_frame,
            wrap="none",
            undo=True,
            font=("Consolas", 10),
            bg="white",
            fg="black",
            insertbackground="black",
            relief="sunken",
            bd=2,
            highlightthickness=0,
        )

        self.code_text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        button_frame = ttk.Frame(parent)
        button_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(6,0)
        )

        button_frame.columnconfigure(0, weight=1)

        tk.Button(
            button_frame,
            text="Clear Code",
            command=self.clear_code,
            bg="#d4d0c8",
            activebackground="#d4d0c8",
            relief="raised",
            bd=2,
            highlightthickness=0,
            padx=10,
            pady=2,
        ).pack(side="left")

        y_scroll = ttk.Scrollbar(
            code_frame,
            orient="vertical",
            command=self.code_text.yview,
        )

        y_scroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        x_scroll = ttk.Scrollbar(
            code_frame,
            orient="horizontal",
            command=self.code_text.xview,
        )

        x_scroll.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.code_text.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

    # =========================================================
    # Ollama loading screen
    # =========================================================

    def show_ollama_loading_screen(self):
        self.loading_window = tk.Toplevel(self)
        self.loading_window.title("Starting AI")
        self.loading_window.geometry("360x140")
        self.loading_window.resizable(False, False)
        self.loading_window.configure(bg="#d4d0c8")
        self.loading_window.transient(self)
        self.loading_window.grab_set()

        self.loading_window.protocol("WM_DELETE_WINDOW", lambda: None)

        ttk.Label(
            self.loading_window,
            text="Starting Ollama AI engine...\nPlease wait.",
            anchor="center",
        ).pack(pady=18)

        self.loading_progress = ttk.Progressbar(
            self.loading_window,
            mode="indeterminate",
        )

        self.loading_progress.pack(
            fill="x",
            padx=30
        )

        self.loading_progress.start(10)

        self.status_var.set("Starting Ollama...")

        thread = threading.Thread(
            target=self.start_ollama_background,
            daemon=True,
        )

        thread.start()

    def start_ollama_background(self):
        started = start_ollama_server()

        if not started:
            self.after(0, self.ollama_failed)
            return

        for _ in range(60):
            if is_ollama_ready():
                self.after(0, self.ollama_ready)
                return

            time.sleep(1)

        self.after(0, self.ollama_failed)

    def ollama_ready(self):
        self.ollama_ready_flag = True

        try:
            self.loading_progress.stop()
            self.loading_window.destroy()
        except Exception:
            pass

        self.status_var.set("Ollama ready")

    def ollama_failed(self):
        self.ollama_ready_flag = False

        try:
            self.loading_progress.stop()
            self.loading_window.destroy()
        except Exception:
            pass

        messagebox.showerror(
            "Ollama Error",
            (
                "Ollama could not be started.\n\n"
                "Make sure Ollama is installed and added to PATH."
            ),
        )

        self.status_var.set("Ollama failed to start")

    # =========================================================
    # Parameter panel
    # =========================================================

    def update_param_scroll_region(self, event=None):
        self.param_canvas.configure(
            scrollregion=self.param_canvas.bbox("all")
        )

    def update_param_canvas_width(self, event):
        self.param_canvas.itemconfigure(
            self.param_window,
            width=event.width
        )

    def build_parameter_fields(self, shape_type):
        for child in self.params_frame.winfo_children():
            child.destroy()

        self.param_vars = {}

        defaults = get_default_params(shape_type)

        if not defaults:
            ttk.Label(
                self.params_frame,
                text="No parameters for this shape.",
            ).grid(
                row=0,
                column=0,
                sticky="w"
            )

            return

        self.params_frame.columnconfigure(1, weight=1)

        for row, (param_name, default_value) in enumerate(defaults.items()):
            label = ttk.Label(
                self.params_frame,
                text=param_name
            )

            label.grid(
                row=row,
                column=0,
                sticky="w",
                pady=4,
                padx=(0, 8)
            )

            var = tk.StringVar(
                value=str(default_value)
            )

            entry = ttk.Entry(
                self.params_frame,
                textvariable=var
            )

            entry.grid(
                row=row,
                column=1,
                sticky="ew",
                pady=4
            )

            self.param_vars[param_name] = var

    # =========================================================
    # Parameter extraction
    # =========================================================

    def get_parameter_values(self):
        values = {}

        for name, var in self.param_vars.items():
            raw_value = var.get().strip()

            if raw_value == "":
                raise ValueError(
                    f"Missing value for parameter: {name}"
                )

            try:
                if name.endswith("count") or name == "teeth":
                    values[name] = int(float(raw_value))
                else:
                    values[name] = float(raw_value)

            except ValueError:
                raise ValueError(
                    f"Invalid number for {name}: {raw_value}"
                )

        return values

    # =========================================================
    # AI detection
    # =========================================================

    def detect_shape(self):
        if not self.ollama_ready_flag:
            messagebox.showwarning(
                "AI Loading",
                "Ollama is still starting. Please wait."
            )
            return False

        prompt = self.prompt_entry.get().strip()

        if not prompt:
            messagebox.showwarning(
                "Missing Prompt",
                "Type a prompt first."
            )

            return False

        try:
            result = classify(prompt)

            operation = result.get("operation")
            shape = result.get("shape")

            if operation != "create_shape":
                messagebox.showinfo(
                    "Operation Detected",
                    (
                        f"Detected operation: {operation}\n\n"
                        "This app currently only creates new objects."
                    ),
                )

                self.status_var.set(
                    f"Detected operation: {operation}"
                )

                return False

            if not shape or shape == "unknown":
                messagebox.showwarning(
                    "Unknown Shape",
                    "The AI could not recognize the object type.",
                )

                self.status_var.set("Unknown shape")

                return False

            if shape not in DEFAULT_PARAMS:
                messagebox.showwarning(
                    "Unsupported Shape",
                    f"Unsupported shape: {shape}",
                )

                self.status_var.set(
                    f"Unsupported shape: {shape}"
                )

                return False

            self.current_shape = shape
            self.build_parameter_fields(shape)

            self.status_var.set(
                f"Detected shape: {shape}"
            )

            return True

        except Exception as error:
            messagebox.showerror(
                "Detection Error",
                str(error)
            )

            self.status_var.set(
                "Detection failed"
            )

            return False

    # =========================================================
    # Generate code
    # =========================================================

    def generate_code(self):
        detected = self.detect_shape()

        if not detected:
            return False

        shape_type = self.current_shape

        try:
            values = self.get_parameter_values()

            code = generate_freecad_code(
                shape_type,
                values
            )

            self.code_text.delete(
                "1.0",
                tk.END
            )

            self.code_text.insert(
                "1.0",
                code
            )

            self.status_var.set(
                f"Generated FreeCAD code for: {shape_type}"
            )

            return True

        except Exception as error:
            messagebox.showerror(
                "Generation Error",
                str(error)
            )

            self.status_var.set(
                "Code generation failed"
            )

            return False

    # =========================================================
    # Copy / Save
    # =========================================================

    def copy_code(self):
        code = self.code_text.get(
            "1.0",
            tk.END
        ).strip()

        if not code:
            messagebox.showwarning(
                "No Code",
                "Generate code first."
            )

            return

        self.clipboard_clear()
        self.clipboard_append(code)
        self.update()

        self.status_var.set(
            "Code copied to clipboard"
        )

    def save_code(self):
        code = self.code_text.get(
            "1.0",
            tk.END
        ).strip()

        if not code:
            messagebox.showwarning(
                "No Code",
                "Generate code first."
            )

            return

        path = filedialog.asksaveasfilename(
            title="Save FreeCAD Python Script",
            defaultextension=".py",
            filetypes=[
                ("Python Files", "*.py"),
                ("All Files", "*.*"),
            ],
        )

        if not path:
            return

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(code)

        self.status_var.set(
            f"Saved script: {path}"
        )

    # =========================================================
    # Macro creation
    # =========================================================

    def create_temp_macro(self, code):
        temp_dir = tempfile.gettempdir()

        macro_path = os.path.join(
            temp_dir,
            f"ai_cad_generated_macro_{int(time.time() * 1000)}.py"
        )

        with open(
            macro_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(code)

        return macro_path

    # =========================================================
    # Run in FreeCAD
    # =========================================================

    def get_or_generate_code(self):
        generated = self.generate_code()

        if not generated:
            return ""

        return self.code_text.get(
            "1.0",
            tk.END
        ).strip()

    def run_in_freecad(self, mode="current"):
        code = self.get_or_generate_code()

        if not code:
            messagebox.showwarning(
                "No Code",
                "Generate code first."
            )

            return

        if not os.path.exists(FREECAD_EXE):
            messagebox.showerror(
                "FreeCAD Not Found",
                (
                    "FreeCAD was not found at:\n\n"
                    + FREECAD_EXE
                ),
            )

            return

        try:
            macro_path = self.create_temp_macro(code)

            if mode == "current":
                subprocess.Popen([
                    FREECAD_EXE,
                    "--single-instance",
                    macro_path
                ])

                self.status_var.set(
                    "Opened macro in current FreeCAD window"
                )

            elif mode == "new":
                subprocess.Popen([
                    FREECAD_EXE,
                    macro_path
                ])

                self.status_var.set(
                    "Opened macro in new FreeCAD window"
                )

            else:
                messagebox.showerror(
                    "Invalid Mode",
                    f"Unknown mode: {mode}"
                )

        except Exception as error:
            messagebox.showerror(
                "Run Error",
                str(error)
            )

            self.status_var.set(
                "Failed to run FreeCAD"
            )

    # =========================================================
    # Close app
    # =========================================================

    def on_close(self):
        stop_ollama_server()
        self.destroy()


# =============================================================
# Main
# =============================================================

def main():
    app = AICADCodeGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
