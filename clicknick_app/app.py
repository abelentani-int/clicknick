"""Tkinter GUI: toolbar, sidebar of insertable commands, nested command
tree (loop/if blocks render as expandable branches), and file I/O."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pynput import keyboard, mouse

from . import commands, dialogs
from .player import Player
from .recorder import Recorder
from .storage import load_macro, save_macro

RECORD_HOTKEY = keyboard.Key.f9
PLAY_HOTKEY = keyboard.Key.f10


class MacroTree:
    """Wraps a ttk.Treeview and keeps it in sync with the nested step list."""

    def __init__(self, parent, on_change=None):
        columns = ("index", "delay", "command")
        self.tree = ttk.Treeview(parent, columns=columns, show="tree headings")
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=0, stretch=False)
        self.tree.heading("index", text="#")
        self.tree.heading("delay", text="Delay (s)")
        self.tree.heading("command", text="Command")
        self.tree.column("index", width=40, anchor=tk.CENTER)
        self.tree.column("delay", width=70, anchor=tk.CENTER)
        self.tree.column("command", width=480, anchor=tk.W)
        self.steps = []
        self.item_info = {}
        self.on_change = on_change

    def pack(self, **kwargs):
        self.tree.pack(**kwargs)

    def set_steps(self, steps):
        self.steps = steps
        self.rebuild()

    def rebuild(self):
        self.tree.delete(*self.tree.get_children())
        self.item_info = {}
        self._add_steps("", self.steps)
        if self.on_change:
            self.on_change()

    def _add_steps(self, parent_iid, container):
        for idx, cmd in enumerate(container):
            iid = self.tree.insert(
                parent_iid,
                tk.END,
                values=(idx + 1, f"{cmd.get('delay', 0):.2f}", commands.describe(cmd)),
                open=True,
            )
            self.item_info[iid] = {"container": container, "index": idx}
            if cmd["type"] == "loop":
                branch = self.tree.insert(iid, tk.END, values=("", "", "↳ Repeat:"), open=True)
                child_list = commands.loop_children(cmd)
                self.item_info[branch] = {"branch_container": child_list}
                self._add_steps(branch, child_list)
            elif cmd["type"] == "if":
                then_list = commands.then_children(cmd)
                then_branch = self.tree.insert(iid, tk.END, values=("", "", "↳ Then:"), open=True)
                self.item_info[then_branch] = {"branch_container": then_list}
                self._add_steps(then_branch, then_list)

                else_list = commands.else_children(cmd)
                else_branch = self.tree.insert(iid, tk.END, values=("", "", "↳ Else:"), open=True)
                self.item_info[else_branch] = {"branch_container": else_list}
                self._add_steps(else_branch, else_list)

    def insertion_point(self):
        """Where a newly inserted command should land, based on selection."""
        selected = self.tree.selection()
        if not selected:
            return self.steps, len(self.steps)
        info = self.item_info.get(selected[0])
        if info is None:
            return self.steps, len(self.steps)
        if "branch_container" in info:
            container = info["branch_container"]
            return container, len(container)
        return info["container"], info["index"] + 1

    def insert_command(self, cmd):
        container, index = self.insertion_point()
        container.insert(index, cmd)
        self.rebuild()

    def delete_selected(self):
        by_container = {}
        for iid in self.tree.selection():
            info = self.item_info.get(iid)
            if info is None or "index" not in info:
                continue
            by_container.setdefault(id(info["container"]), (info["container"], []))[1].append(
                info["index"]
            )
        for container, indices in by_container.values():
            for idx in sorted(set(indices), reverse=True):
                del container[idx]
        self.rebuild()


# Each entry: (sidebar label, dialog title, field specs). "if" and "loop"
# are handled separately since they create container commands.
SIMPLE_FORMS = {
    "mouse_click": (
        "\U0001F5B1 Click",
        "Insert Mouse Click",
        lambda: [
            {"key": "x", "label": "X", "kind": "int", "default": mouse.Controller().position[0]},
            {"key": "y", "label": "Y", "kind": "int", "default": mouse.Controller().position[1]},
            {"key": "button", "label": "Button", "kind": "choice", "choices": ["left", "right", "middle"], "default": "left"},
            {"key": "double", "label": "Double-click", "kind": "bool", "default": False},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "key_press": (
        "⌨ Key",
        "Insert Key Press",
        lambda: [
            {"key": "key", "label": "Key", "kind": "key", "default": None},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "type_text": (
        "\U0001F4DD Type Text",
        "Insert Type Text",
        lambda: [
            {"key": "text", "label": "Text (use {var} for variables)", "kind": "multiline", "default": ""},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "wait": (
        "⏱ Wait",
        "Insert Wait",
        lambda: [
            {"key": "delay", "label": "Seconds to wait", "kind": "float", "default": 1.0},
        ],
    ),
    "open_program": (
        "\U0001F4C2 Program",
        "Insert Open Program",
        lambda: [
            {"key": "path", "label": "Program path", "kind": "path", "default": ""},
            {"key": "args", "label": "Arguments", "kind": "str", "default": ""},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "open_url": (
        "\U0001F310 Website",
        "Insert Open Website",
        lambda: [
            {"key": "url", "label": "URL", "kind": "str", "default": "https://"},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "focus_window": (
        "\U0001FA9F Window",
        "Insert Focus Window",
        lambda: [
            {"key": "title_contains", "label": "Window title contains", "kind": "str", "default": ""},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "clipboard_set": (
        "\U0001F4CB Set Clip",
        "Insert Set Clipboard",
        lambda: [
            {"key": "text", "label": "Text (use {var} for variables)", "kind": "multiline", "default": ""},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "clipboard_get": (
        "\U0001F4CB Get Clip",
        "Insert Read Clipboard",
        lambda: [
            {"key": "var_name", "label": "Store into variable", "kind": "str", "default": "clip"},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "set_variable": (
        "\U0001F527 Variable",
        "Insert Set Variable",
        lambda: [
            {"key": "name", "label": "Variable name", "kind": "str", "default": "myvar"},
            {"key": "value", "label": "Value", "kind": "str", "default": ""},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "comment": (
        "\U0001F4AC Comment",
        "Insert Comment",
        lambda: [
            {"key": "text", "label": "Note", "kind": "str", "default": ""},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "click_image": (
        "\U0001F5BC Click Image",
        "Insert Click Image",
        lambda: [
            {"key": "image_path", "label": "Reference image", "kind": "image_path", "default": ""},
            {"key": "button", "label": "Button", "kind": "choice", "choices": ["left", "right", "middle"], "default": "left"},
            {"key": "timeout", "label": "Timeout (s)", "kind": "float", "default": 10.0},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "wait_image": (
        "\U0001F50D Wait Image",
        "Insert Wait For Image",
        lambda: [
            {"key": "image_path", "label": "Reference image", "kind": "image_path", "default": ""},
            {"key": "timeout", "label": "Timeout (s)", "kind": "float", "default": 10.0},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
    "find_image": (
        "\U0001F4CD Find Image",
        "Insert Find Image",
        lambda: [
            {"key": "image_path", "label": "Reference image", "kind": "image_path", "default": ""},
            {"key": "var_name", "label": "Store position into variable", "kind": "str", "default": "pos"},
            {"key": "timeout", "label": "Timeout (s)", "kind": "float", "default": 10.0},
            {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
        ],
    ),
}


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ClickNick")
        self.root.geometry("900x560")

        self.recorder = Recorder(stop_key=RECORD_HOTKEY)
        self.player = Player(on_finished=self._on_playback_finished)
        self.current_path = None

        self._build_menu()
        self._build_toolbar()
        self._build_body()
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

        insert_menu = tk.Menu(menubar, tearoff=0)
        for cmd_type, (_icon_label, title, _fields) in SIMPLE_FORMS.items():
            insert_menu.add_command(
                label=title.replace("Insert ", ""), command=lambda t=cmd_type: self.insert_simple(t)
            )
        insert_menu.add_separator()
        insert_menu.add_command(label="Loop", command=self.insert_loop)
        insert_menu.add_command(label="If", command=self.insert_if)
        menubar.add_cascade(label="Insert", menu=insert_menu)

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

    # ---------------------------------------------------------------- body
    def _build_body(self):
        body = ttk.Frame(self.root)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        sidebar = ttk.Frame(body, padding=4)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(sidebar, text="Insert:", font=("", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))
        for cmd_type, (icon_label, _title, _fields) in SIMPLE_FORMS.items():
            ttk.Button(
                sidebar, text=icon_label, width=14, command=lambda t=cmd_type: self.insert_simple(t)
            ).pack(fill=tk.X, pady=1)
        ttk.Separator(sidebar).pack(fill=tk.X, pady=4)
        ttk.Button(sidebar, text="\U0001F501 Loop", width=14, command=self.insert_loop).pack(
            fill=tk.X, pady=1
        )
        ttk.Button(sidebar, text="❓ If", width=14, command=self.insert_if).pack(
            fill=tk.X, pady=1
        )

        table_frame = ttk.Frame(body)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        self.macro_tree = MacroTree(table_frame)
        self.macro_tree.pack(fill=tk.BOTH, expand=True)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W, padding=4).pack(
            side=tk.BOTTOM, fill=tk.X
        )

    # ------------------------------------------------------- insert dialogs
    def insert_simple(self, cmd_type):
        _icon, title, fields_fn = SIMPLE_FORMS[cmd_type]
        values = dialogs.ask_fields(self.root, title, fields_fn())
        if values is None:
            return
        if cmd_type == "key_press" and values.get("key") is None:
            messagebox.showwarning("ClickNick", "No key was set.")
            return
        cmd = {"type": cmd_type}
        cmd.update(values)
        self.macro_tree.insert_command(cmd)

    def insert_loop(self):
        values = dialogs.ask_fields(
            self.root,
            "Insert Loop",
            [
                {"key": "count", "label": "Repeat count (0=infinite)", "kind": "int", "default": 2},
                {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
            ],
        )
        if values is None:
            return
        cmd = {"type": "loop", "count": values["count"], "delay": values["delay"], "children": []}
        self.macro_tree.insert_command(cmd)

    def insert_if(self):
        kind_values = dialogs.ask_fields(
            self.root,
            "Insert If - condition type",
            [
                {
                    "key": "kind",
                    "label": "Condition",
                    "kind": "choice",
                    "choices": ["variable_equals", "variable_contains", "image_found"],
                    "default": "variable_equals",
                }
            ],
        )
        if kind_values is None:
            return
        kind = kind_values["kind"]
        if kind == "image_found":
            fields = [
                {"key": "image_path", "label": "Reference image", "kind": "image_path", "default": ""},
                {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
            ]
        else:
            fields = [
                {"key": "name", "label": "Variable name", "kind": "str", "default": "myvar"},
                {"key": "value", "label": "Value to compare", "kind": "str", "default": ""},
                {"key": "delay", "label": "Delay before (s)", "kind": "float", "default": 0.0},
            ]
        values = dialogs.ask_fields(self.root, "Insert If - condition", fields)
        if values is None:
            return
        delay = values.pop("delay")
        condition = {"kind": kind, **values}
        cmd = {"type": "if", "condition": condition, "delay": delay, "then": [], "else": []}
        self.macro_tree.insert_command(cmd)

    # ------------------------------------------------------------ actions
    def toggle_record(self):
        if self.recorder.recording:
            steps = self.recorder.stop()
            self.macro_tree.set_steps(steps)
            self.record_btn.config(text="● Record (F9)")
            self.status_var.set(f"Recorded {len(steps)} events")
        else:
            if self.player.playing:
                return
            if self.macro_tree.steps and not messagebox.askyesno(
                "ClickNick", "Recording will replace the current macro. Continue?"
            ):
                return
            self.recorder.start()
            self.record_btn.config(text="■ Stop (F9)")
            self.status_var.set("Recording... press F9 to stop")

    def toggle_play(self):
        if self.player.playing:
            self.player.stop()
            return
        if not self.macro_tree.steps:
            messagebox.showinfo("ClickNick", "No macro recorded yet.")
            return
        if self.recorder.recording:
            return
        self.play_btn.config(text="■ Stop (F10)")
        self.status_var.set("Playing...")
        self.player.play(
            self.macro_tree.steps, speed=self.speed_var.get(), loops=self.loops_var.get()
        )

    def _on_playback_finished(self):
        self.root.after(0, self._reset_play_button)

    def _reset_play_button(self):
        self.play_btn.config(text="▶ Play (F10)")
        self.status_var.set("Idle")

    def delete_selected(self):
        self.macro_tree.delete_selected()

    def new_macro(self):
        if self.recorder.recording or self.player.playing:
            return
        self.macro_tree.set_steps([])
        self.current_path = None
        self.status_var.set("Idle")

    def open_macro(self):
        path = filedialog.askopenfilename(filetypes=[("Macro files", "*.macro.json")])
        if not path:
            return
        self.macro_tree.set_steps(load_macro(path))
        self.current_path = path
        self.status_var.set(f"Loaded {os.path.basename(path)}")

    def save_macro(self):
        if self.current_path is None:
            self.save_macro_as()
            return
        save_macro(self.macro_tree.steps, self.current_path)
        self.status_var.set(f"Saved {os.path.basename(self.current_path)}")

    def save_macro_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".macro.json", filetypes=[("Macro files", "*.macro.json")]
        )
        if not path:
            return
        self.current_path = path
        save_macro(self.macro_tree.steps, path)
        self.status_var.set(f"Saved {os.path.basename(path)}")

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "ClickNick\n\n"
            "An original mouse/keyboard macro recorder and player for Windows.\n"
            "Record input, or build macros by hand with the sidebar: clicks, keys, "
            "waits, loops, conditions, clipboard, variables and image recognition.",
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
