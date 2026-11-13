"""Tkinter GUI tying the recorder, player and storage together."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pynput import keyboard

from . import events as ev
from .player import Player
from .recorder import Recorder
from .storage import load_macro, save_macro

RECORD_HOTKEY = keyboard.Key.f9
PLAY_HOTKEY = keyboard.Key.f10


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ClickNick")
        self.root.geometry("640x480")

        self.recorder = Recorder(stop_key=RECORD_HOTKEY)
        self.player = Player(on_finished=self._on_playback_finished)
        self.events = []
        self.current_path = None

        self._build_menu()
        self._build_toolbar()
        self._build_table()
        self._build_statusbar()

        self._hotkey_listener = keyboard.Listener(on_press=self._on_global_hotkey)
        self._hotkey_listener.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------------- menu
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_macro)
        file_menu.add_command(label="Open...", command=self.open_macro)
        file_menu.add_command(label="Save", command=self.save_macro)
        file_menu.add_command(label="Save As...", command=self.save_macro_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Delete Selected", command=self.delete_selected)
        edit_menu.add_command(label="Clear All", command=self.new_macro)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # ------------------------------------------------------------- toolbar
    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(side=tk.TOP, fill=tk.X)

        self.record_btn = ttk.Button(bar, text="● Record (F9)", command=self.toggle_record)
        self.record_btn.pack(side=tk.LEFT, padx=2)

        self.play_btn = ttk.Button(bar, text="▶ Play (F10)", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        ttk.Label(bar, text="Speed:").pack(side=tk.LEFT, padx=(16, 2))
        self.speed_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(
            bar, from_=0.1, to=10.0, increment=0.1, width=5, textvariable=self.speed_var
        ).pack(side=tk.LEFT)

        ttk.Label(bar, text="Loops (0=infinite):").pack(side=tk.LEFT, padx=(16, 2))
        self.loops_var = tk.IntVar(value=1)
        ttk.Spinbox(bar, from_=0, to=9999, width=6, textvariable=self.loops_var).pack(
            side=tk.LEFT
        )

    # --------------------------------------------------------------- table
    def _build_table(self):
        columns = ("index", "time", "command")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.heading("index", text="#")
        self.tree.heading("time", text="Time (s)")
        self.tree.heading("command", text="Command")
        self.tree.column("index", width=40, anchor=tk.CENTER)
        self.tree.column("time", width=80, anchor=tk.CENTER)
        self.tree.column("command", width=480, anchor=tk.W)
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W, padding=4).pack(
            side=tk.BOTTOM, fill=tk.X
        )

    # ------------------------------------------------------------ actions
    def toggle_record(self):
        if self.recorder.recording:
            self.events = self.recorder.stop()
            self._refresh_table()
            self.record_btn.config(text="● Record (F9)")
            self.status_var.set(f"Recorded {len(self.events)} events")
        else:
            if self.player.playing:
                return
            self.recorder.start()
            self.record_btn.config(text="■ Stop (F9)")
            self.status_var.set("Recording... press F9 to stop")

    def toggle_play(self):
        if self.player.playing:
            self.player.stop()
            return
        if not self.events:
            messagebox.showinfo("ClickNick", "No macro recorded yet.")
            return
        if self.recorder.recording:
            return
        self.play_btn.config(text="■ Stop (F10)")
        self.status_var.set("Playing...")
        self.player.play(self.events, speed=self.speed_var.get(), loops=self.loops_var.get())

    def _on_playback_finished(self):
        self.root.after(0, self._reset_play_button)

    def _reset_play_button(self):
        self.play_btn.config(text="▶ Play (F10)")
        self.status_var.set("Idle")

    def delete_selected(self):
        selected = self.tree.selection()
        indices = sorted((int(self.tree.item(i, "values")[0]) - 1 for i in selected), reverse=True)
        for idx in indices:
            del self.events[idx]
        self._refresh_table()

    def new_macro(self):
        if self.recorder.recording or self.player.playing:
            return
        self.events = []
        self.current_path = None
        self._refresh_table()
        self.status_var.set("Idle")

    def open_macro(self):
        path = filedialog.askopenfilename(filetypes=[("Macro files", "*.macro.json")])
        if not path:
            return
        self.events = load_macro(path)
        self.current_path = path
        self._refresh_table()
        self.status_var.set(f"Loaded {os.path.basename(path)}")

    def save_macro(self):
        if self.current_path is None:
            self.save_macro_as()
            return
        save_macro(self.events, self.current_path)
        self.status_var.set(f"Saved {os.path.basename(self.current_path)}")

    def save_macro_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".macro.json", filetypes=[("Macro files", "*.macro.json")]
        )
        if not path:
            return
        self.current_path = path
        save_macro(self.events, path)
        self.status_var.set(f"Saved {os.path.basename(path)}")

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, event in enumerate(self.events, start=1):
            self.tree.insert(
                "", tk.END, values=(i, f"{event['t']:.3f}", ev.describe(event))
            )

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "ClickNick\n\n"
            "An original mouse/keyboard macro recorder and player for Windows.\n"
            "Records global input events and replays them with adjustable speed and looping.",
        )

    # --------------------------------------------------------------- misc
    def _on_global_hotkey(self, key):
        if key == RECORD_HOTKEY:
            self.root.after(0, self.toggle_record)
        elif key == PLAY_HOTKEY:
            self.root.after(0, self.toggle_play)

    def _on_close(self):
        if self.recorder.recording:
            self.recorder.stop()
        if self.player.playing:
            self.player.stop()
        self._hotkey_listener.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
