"""Serialization helpers between pynput objects and plain JSON-safe dicts."""

from pynput import keyboard, mouse


def key_to_str(key):
    if isinstance(key, keyboard.KeyCode):
        if key.char is not None:
            return f"char:{key.char}"
        return f"vk:{key.vk}"
    return f"special:{key.name}"


def str_to_key(value):
    kind, _, payload = value.partition(":")
    if kind == "char":
        return keyboard.KeyCode.from_char(payload)
    if kind == "vk":
        return keyboard.KeyCode.from_vk(int(payload))
    return keyboard.Key[payload]


def button_to_str(button):
    return button.name


def str_to_button(value):
    return mouse.Button[value]


def key_label(value):
    """Short human-readable label for a key_to_str() value."""
    kind, _, payload = value.partition(":")
    if kind == "char":
        return payload
    if kind == "vk":
        return f"VK {payload}"
    return payload


def describe(event):
    """Human-readable one-line summary for the command list UI."""
    t = event["type"]
    if t == "move":
        return f"Move mouse to ({event['x']}, {event['y']})"
    if t == "click":
        action = "Press" if event["pressed"] else "Release"
        return f"{action} {event['button']} click at ({event['x']}, {event['y']})"
    if t == "scroll":
        return f"Scroll at ({event['x']}, {event['y']}) dx={event['dx']} dy={event['dy']}"
    if t == "key_down":
        return f"Key down: {event['key']}"
    if t == "key_up":
        return f"Key up: {event['key']}"
    return t
