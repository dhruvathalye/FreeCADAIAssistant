"""
app.py

Standalone AI CAD Code Generator for FreeCAD.

Required files in the same folder:
- app.py
- classifier.py
- generators.py
"""

import os
import subprocess
import tempfile
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from classifier import classify, SUPPORTED_TYPES
from generators import DEFAULT_PARAMS, generate_freecad_code, get_default_params


APP_TITLE = "AI CAD Code Generator for FreeCAD"
FREECAD_EXE = r"C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe"


class AICADCodeGeneratorApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1150x760")
        self.minsize(950, 620)

        self.shape_type_var = tk.StringVar(value="rectangle")
        self.param_vars = {}

        self.create_widgets()
        self.build_parameter_fields("rectangle")

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

        self.prompt_entry.insert(
            0,
            "make a sprocket"
        )

        ttk.Button(
            top_frame,
            text="Detect Shape with AI",
            command=self.detect_shape,
        ).grid(row=0, column=2, padx=4)

        ttk.Button(
            top_frame,
            text="Generate Code",
            command=self.generate_code,
        ).grid(row=0, column=3, padx=4)

        ttk.Button(
            top_frame,
            text="Copy Code",
            command=self.copy_code,
        ).grid(row=0, column=4, padx=4)

        ttk.Button(
            top_frame,
            text="Save .py",
            command=self.save_code,
        ).grid(row=0, column=5, padx=4)

        # -----------------------------------------------------
        # Run button menu
        # -----------------------------------------------------

        run_button = ttk.Menubutton(
            top_frame,
            text="Run in FreeCAD"
        )

        run_menu = tk.Menu(
            run_button,
            tearoff=0
        )

        run_menu.add_command(
            label="Open in Current FreeCAD Window",
            command=lambda: self.run_in_freecad(
                mode="current"
            ),
        )

        run_menu.add_command(
            label="Open in New FreeCAD Window",
            command=lambda: self.run_in_freecad(
                mode="new"
            ),
        )

        run_button["menu"] = run_menu

        run_button.grid(
            row=0,
            column=6,
            padx=4
        )

        # -----------------------------------------------------
        # Main panels
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Status bar
        # -----------------------------------------------------

        self.status_var = tk.StringVar(
            value="Ready"
        )

        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=5,
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
        parent.rowconfigure(3, weight=1)

        ttk.Label(
            parent,
            text="Detected / Selected Shape:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.shape_combo = ttk.Combobox(
            parent,
            textvariable=self.shape_type_var,
            values=SUPPORTED_TYPES,
            state="readonly",
        )

        self.shape_combo.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(3, 12)
        )

        self.shape_combo.bind(
            "<<ComboboxSelected>>",
            self.on_shape_changed
        )

        ttk.Label(
            parent,
            text="Parameters:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
        )

        param_outer = ttk.Frame(parent)

        param_outer.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

        param_outer.columnconfigure(0, weight=1)
        param_outer.rowconfigure(0, weight=1)

        self.param_canvas = tk.Canvas(
            param_outer,
            highlightthickness=0
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
        )

        self.code_text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

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

    def on_shape_changed(self, event=None):

        shape_type = self.shape_type_var.get()
        self.build_parameter_fields(shape_type)

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

        prompt = self.prompt_entry.get().strip()

        if not prompt:

            messagebox.showwarning(
                "Missing Prompt",
                "Type a prompt first."
            )

            return

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

                return

            if not shape or shape == "unknown":

                messagebox.showwarning(
                    "Unknown Shape",
                    "The AI could not recognize the object type.",
                )

                self.status_var.set("Unknown shape")

                return

            if shape not in DEFAULT_PARAMS:

                messagebox.showwarning(
                    "Unsupported Shape",
                    f"Unsupported shape: {shape}",
                )

                self.status_var.set(
                    f"Unsupported shape: {shape}"
                )

                return

            self.shape_type_var.set(shape)
            self.build_parameter_fields(shape)

            self.status_var.set(
                f"Detected shape: {shape}"
            )

        except Exception as error:

            messagebox.showerror(
                "Detection Error",
                str(error)
            )

            self.status_var.set(
                "Detection failed"
            )

    # =========================================================
    # Generate code
    # =========================================================

    def generate_code(self):

        shape_type = self.shape_type_var.get()

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

        except Exception as error:

            messagebox.showerror(
                "Generation Error",
                str(error)
            )

            self.status_var.set(
                "Code generation failed"
            )

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

        # ALWAYS regenerate
        self.detect_shape()
        self.generate_code()

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

            # -------------------------------------------------
            # CURRENT WINDOW
            # -------------------------------------------------

            if mode == "current":
                subprocess.Popen([
                    FREECAD_EXE,
                    "--single-instance",
                    macro_path
                ])

                self.status_var.set("Opened macro in current FreeCAD window")

            # -------------------------------------------------
            # NEW WINDOW
            # -------------------------------------------------

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


# =============================================================
# Main
# =============================================================

def main():

    app = AICADCodeGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()