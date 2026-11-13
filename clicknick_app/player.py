"""Executes a command list: plain actions, recorded input, and nested
loop/if blocks, with variable substitution and screen-image matching."""

import shlex
import subprocess
import threading
import webbrowser

from pynput import keyboard, mouse

from . import clipboard, commands, events as ev, vision, window_utils
from .variables import VariableStore


class Context:
    def __init__(self, speed, stop_flag):
        self.mouse = mouse.Controller()
        self.keyboard = keyboard.Controller()
        self.variables = VariableStore()
        self.speed = speed
        self.stop_flag = stop_flag


class Player:
    def __init__(self, on_finished=None):
        self.on_finished = on_finished
        self._stop_flag = threading.Event()
        self._thread = None
        self.playing = False

    def play(self, steps, speed=1.0, loops=1):
        if self.playing or not steps:
            return
        self.playing = True
        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._run, args=(steps, speed, loops), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_flag.set()

    def _run(self, steps, speed, loops):
        ctx = Context(speed, self._stop_flag)
        infinite = loops <= 0
        count = 0
        try:
            while (infinite or count < loops) and not self._stop_flag.is_set():
                run_steps(steps, ctx)
                count += 1
        finally:
            self.playing = False
            if self.on_finished is not None:
                self.on_finished()


def run_steps(steps, ctx):
    for step in steps:
        if ctx.stop_flag.is_set():
            return
        delay = step.get("delay", 0) / ctx.speed
        if delay > 0:
            ctx.stop_flag.wait(delay)
            if ctx.stop_flag.is_set():
                return
        run_one(step, ctx)


def run_one(step, ctx):
    t = step["type"]
    sub = ctx.variables.substitute

    if t == "move":
        ctx.mouse.position = (step["x"], step["y"])
    elif t == "click":
        ctx.mouse.position = (step["x"], step["y"])
        button = ev.str_to_button(step["button"])
        if step["pressed"]:
            ctx.mouse.press(button)
        else:
            ctx.mouse.release(button)
    elif t == "scroll":
        ctx.mouse.position = (step["x"], step["y"])
        ctx.mouse.scroll(step["dx"], step["dy"])
    elif t == "key_down":
        ctx.keyboard.press(ev.str_to_key(step["key"]))
    elif t == "key_up":
        ctx.keyboard.release(ev.str_to_key(step["key"]))
    elif t == "mouse_click":
        _mouse_click(step, ctx)
    elif t == "key_press":
        key = ev.str_to_key(step["key"])
        ctx.keyboard.press(key)
        ctx.keyboard.release(key)
    elif t == "type_text":
        ctx.keyboard.type(sub(step["text"]))
    elif t == "wait":
        pass  # the delay above already covers it
    elif t == "open_program":
        args = shlex.split(sub(step.get("args", "")))
        subprocess.Popen([sub(step["path"]), *args])
    elif t == "open_url":
        webbrowser.open(sub(step["url"]))
    elif t == "focus_window":
        window_utils.focus_window(sub(step["title_contains"]))
    elif t == "clipboard_set":
        clipboard.set_text(sub(step["text"]))
    elif t == "clipboard_get":
        ctx.variables.set(step["var_name"], clipboard.get_text())
    elif t == "set_variable":
        ctx.variables.set(step["name"], sub(step["value"]))
    elif t == "comment":
        pass
    elif t == "click_image":
        _click_image(step, ctx)
    elif t == "wait_image":
        vision.wait_for_image(step["image_path"], step.get("timeout", 10.0), stop_flag=ctx.stop_flag)
    elif t == "find_image":
        match = vision.wait_for_image(
            step["image_path"], step.get("timeout", 10.0), stop_flag=ctx.stop_flag
        )
        ctx.variables.set(step["var_name"], f"{match[0]},{match[1]}" if match else "")
    elif t == "loop":
        _run_loop(step, ctx)
    elif t == "if":
        _run_if(step, ctx)


def _mouse_click(step, ctx):
    ctx.mouse.position = (step["x"], step["y"])
    button = ev.str_to_button(step["button"])
    clicks = 2 if step.get("double") else 1
    for _ in range(clicks):
        ctx.mouse.click(button)


def _click_image(step, ctx):
    match = vision.wait_for_image(
        step["image_path"], step.get("timeout", 10.0), stop_flag=ctx.stop_flag
    )
    if match is None:
        return
    x, y, _, _ = match
    ctx.mouse.position = (x, y)
    ctx.mouse.click(ev.str_to_button(step.get("button", "left")))


def _run_loop(step, ctx):
    children = commands.loop_children(step)
    count = step.get("count", 0)
    infinite = count <= 0
    i = 0
    while (infinite or i < count) and not ctx.stop_flag.is_set():
        run_steps(children, ctx)
        i += 1


def _run_if(step, ctx):
    branch = commands.then_children(step) if evaluate(step["condition"], ctx) else commands.else_children(step)
    run_steps(branch, ctx)


def evaluate(cond, ctx):
    kind = cond["kind"]
    if kind == "variable_equals":
        return ctx.variables.get(cond["name"]) == cond["value"]
    if kind == "variable_contains":
        return cond["value"] in ctx.variables.get(cond["name"])
    if kind == "image_found":
        return vision.find_on_screen(cond["image_path"]) is not None
    return False
