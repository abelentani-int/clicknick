from pynput import keyboard, mouse

from clicknick_app import events as ev


def test_char_key_roundtrip():
    key = keyboard.KeyCode.from_char("a")
    assert ev.str_to_key(ev.key_to_str(key)).char == "a"


def test_special_key_roundtrip():
    key = keyboard.Key.f9
    assert ev.str_to_key(ev.key_to_str(key)) == keyboard.Key.f9


def test_button_roundtrip():
    button = mouse.Button.left
    assert ev.str_to_button(ev.button_to_str(button)) == mouse.Button.left


def test_describe_click():
    event = {"type": "click", "x": 10, "y": 20, "button": "left", "pressed": True}
    assert "Press left click at (10, 20)" == ev.describe(event)
