"""Shared metadata for every command type: human descriptions and which
ones are containers (blocks) that hold a nested list of child commands."""

from . import events as ev

BLOCK_TYPES = {"loop", "if"}


def is_block(cmd):
    return cmd.get("type") in BLOCK_TYPES


def loop_children(cmd):
    return cmd.setdefault("children", [])


def then_children(cmd):
    return cmd.setdefault("then", [])


def else_children(cmd):
    return cmd.setdefault("else", [])


def describe(cmd):
    t = cmd["type"]
    if t in ("move", "click", "scroll", "key_down", "key_up"):
        return ev.describe(cmd)
    if t == "mouse_click":
        kind = "Double-click" if cmd.get("double") else "Click"
        return f"{kind} {cmd['button']} at ({cmd['x']}, {cmd['y']})"
    if t == "key_press":
        return f"Press key: {ev.key_label(cmd['key'])}"
    if t == "type_text":
        return f'Type text: "{cmd["text"]}"'
    if t == "wait":
        return f"Wait {cmd['delay']:.2f}s"
    if t == "open_program":
        return f"Open program: {cmd['path']}"
    if t == "open_url":
        return f"Open website: {cmd['url']}"
    if t == "focus_window":
        return f"Focus window containing: \"{cmd['title_contains']}\""
    if t == "clipboard_set":
        return f'Set clipboard to: "{cmd["text"]}"'
    if t == "clipboard_get":
        return f"Read clipboard into variable: {cmd['var_name']}"
    if t == "set_variable":
        return f"Set variable {cmd['name']} = \"{cmd['value']}\""
    if t == "comment":
        return f"# {cmd['text']}"
    if t == "click_image":
        return f"Click image: {cmd['image_path']}"
    if t == "wait_image":
        return f"Wait for image: {cmd['image_path']} (timeout {cmd['timeout']}s)"
    if t == "find_image":
        return f"Find image {cmd['image_path']} -> variable {cmd['var_name']}"
    if t == "loop":
        count = cmd.get("count", 0)
        label = "infinite" if count <= 0 else f"{count}x"
        return f"Loop ({label})"
    if t == "if":
        return f"If {describe_condition(cmd['condition'])}"
    return t


def describe_condition(cond):
    kind = cond.get("kind")
    if kind == "variable_equals":
        return f"{cond['name']} == \"{cond['value']}\""
    if kind == "variable_contains":
        return f"{cond['name']} contains \"{cond['value']}\""
    if kind == "image_found":
        return f"image found: {cond['image_path']}"
    return kind
