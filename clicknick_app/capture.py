"""Interactive drag-to-select screen region, saved as a reference PNG for
the image-recognition commands (click_image / wait_image / find_image)."""

import os
import time
import tkinter as tk
from tkinter import simpledialog

from . import vision

CAPTURES_DIR = os.path.join(os.getcwd(), "captures")


def _select_region(root):
    """Shows a full-screen overlay, returns (left, top, right, bottom) in
    screen coordinates, or None if the user cancelled (Escape)."""
    result = {"bbox": None}
    start = {}

    overlay = tk.Toplevel(root)
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.25)
    overlay.configure(bg="black")
    overlay.attributes("-topmost", True)
    overlay.config(cursor="cross")

    canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    rect_id = None

    def on_press(event):
        start["x"], start["y"] = event.x_root, event.y_root

    def on_drag(event):
        nonlocal rect_id
        if rect_id is not None:
            canvas.delete(rect_id)
        x0, y0 = start["x"] - overlay.winfo_rootx(), start["y"] - overlay.winfo_rooty()
        x1, y1 = event.x_root - overlay.winfo_rootx(), event.y_root - overlay.winfo_rooty()
        rect_id = canvas.create_rectangle(x0, y0, x1, y1, outline="red", width=2)

    def on_release(event):
        x0, y0 = start.get("x"), start.get("y")
        x1, y1 = event.x_root, event.y_root
        overlay.destroy()
        if x0 is None:
            return
        result["bbox"] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

    def on_escape(_event):
        overlay.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    overlay.bind("<Escape>", on_escape)
    overlay.focus_force()
    overlay.wait_window()
    return result["bbox"]


def capture_region_to_file(root):
    """Runs the interactive selection, saves the grabbed region as a PNG
    under ./captures, and returns its path (or None if cancelled)."""
    root.withdraw()
    time.sleep(0.2)  # let the main window actually disappear before grabbing
    try:
        bbox = _select_region(root)
    finally:
        root.deiconify()
    if bbox is None or bbox[2] - bbox[0] < 2 or bbox[3] - bbox[1] < 2:
        return None

    os.makedirs(CAPTURES_DIR, exist_ok=True)
    name = simpledialog.askstring(
        "Save reference image", "File name for this image:", parent=root, initialvalue="reference"
    )
    if not name:
        return None
    if not name.lower().endswith(".png"):
        name += ".png"
    path = os.path.join(CAPTURES_DIR, name)
    image = vision.grab_region(bbox)
    image.save(path)
    return path
