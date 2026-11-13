"""A small generic form dialog: declare fields, get back a dict of values.

Keeps every "insert <command>" dialog in app.py to one declarative call
instead of a bespoke Toplevel class per command type.
"""

import tkinter as tk
from tkinter import filedialog, ttk

from pynput import keyboard

from . import events as ev
from .capture import capture_region_to_file

IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]


def ask_fields(parent, title, field_specs):
    """field_specs: list of dicts with at least {key, label, kind, default}.
    kind in: str, multiline, int, float, bool, choice, path, image_path, key.
    Returns a dict of key -> value, or None if the user cancelled."""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    vars_by_key = {}
    getters = {}
    row = 0
    for spec in field_specs:
        key, label, kind = spec["key"], spec["label"], spec["kind"]
        default = spec.get("default", "")
        ttk.Label(dialog, text=label).grid(row=row, column=0, sticky=tk.W, padx=8, pady=4)

        if kind == "bool":
            var = tk.BooleanVar(value=bool(default))
            ttk.Checkbutton(dialog, variable=var).grid(row=row, column=1, sticky=tk.W, padx=8)
            getters[key] = var.get
        elif kind == "choice":
            var = tk.StringVar(value=default or spec["choices"][0])
            ttk.Combobox(
                dialog, textvariable=var, values=spec["choices"], state="readonly", width=18
            ).grid(row=row, column=1, padx=8)
            getters[key] = var.get
        elif kind == "multiline":
            text = tk.Text(dialog, width=40, height=4)
            text.insert("1.0", str(default))
            text.grid(row=row, column=1, padx=8, pady=4)
            getters[key] = lambda t=text: t.get("1.0", tk.END).rstrip("\n")
        elif kind in ("int", "float"):
            var = tk.StringVar(value=str(default))
            ttk.Entry(dialog, textvariable=var, width=20).grid(row=row, column=1, padx=8)
            caster = int if kind == "int" else float
            getters[key] = lambda v=var, c=caster: c(v.get() or 0)
        elif kind == "path":
            var = tk.StringVar(value=str(default))
            frame = ttk.Frame(dialog)
            frame.grid(row=row, column=1, padx=8, sticky=tk.W)
            ttk.Entry(frame, textvariable=var, width=30).pack(side=tk.LEFT)

            def browse(v=var):
                chosen = filedialog.askopenfilename()
                if chosen:
                    v.set(chosen)

            ttk.Button(frame, text="Browse...", command=browse).pack(side=tk.LEFT, padx=4)
            getters[key] = var.get
        elif kind == "image_path":
            var = tk.StringVar(value=str(default))
            frame = ttk.Frame(dialog)
            frame.grid(row=row, column=1, padx=8, sticky=tk.W)
            ttk.Entry(frame, textvariable=var, width=26).pack(side=tk.LEFT)

            def browse(v=var):
                chosen = filedialog.askopenfilename(filetypes=IMAGE_FILETYPES)
                if chosen:
                    v.set(chosen)

            def capture(v=var):
                path = capture_region_to_file(parent)
                if path:
                    v.set(path)

            ttk.Button(frame, text="Browse...", command=browse).pack(side=tk.LEFT, padx=2)
            ttk.Button(frame, text="Capture...", command=capture).pack(side=tk.LEFT, padx=2)
            getters[key] = var.get
        elif kind == "key":
            label_var = tk.StringVar(value=ev.key_label(default) if default else "(none)")
            captured = {"value": default}
            frame = ttk.Frame(dialog)
            frame.grid(row=row, column=1, padx=8, sticky=tk.W)
            ttk.Label(frame, textvariable=label_var, width=12).pack(side=tk.LEFT)

            def start_capture():
                label_var.set("press a key...")

                def on_press(key):
                    serialized = ev.key_to_str(key)
                    captured["value"] = serialized
                    dialog.after(0, lambda: label_var.set(ev.key_label(serialized)))
                    return False  # stop listener after one key

                listener = keyboard.Listener(on_press=on_press)
                listener.start()

            ttk.Button(frame, text="Set key...", command=start_capture).pack(side=tk.LEFT, padx=4)
            getters[key] = lambda c=captured: c["value"]
        else:  # "str"
            var = tk.StringVar(value=str(default))
            ttk.Entry(dialog, textvariable=var, width=32).grid(row=row, column=1, padx=8)
            getters[key] = var.get

        row += 1

    result = {}

    def on_ok():
        for spec in field_specs:
            result[spec["key"]] = getters[spec["key"]]()
        dialog.destroy()

    def on_cancel():
        result.clear()
        result["__cancelled__"] = True
        dialog.destroy()

    button_row = ttk.Frame(dialog)
    button_row.grid(row=row, column=0, columnspan=2, pady=10)
    ttk.Button(button_row, text="OK", command=on_ok).pack(side=tk.LEFT, padx=6)
    ttk.Button(button_row, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=6)

    dialog.bind("<Return>", lambda _e: on_ok())
    dialog.bind("<Escape>", lambda _e: on_cancel())
    dialog.wait_window()

    if result.get("__cancelled__"):
        return None
    return result
