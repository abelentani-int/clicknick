"""Captures global mouse and keyboard activity into a list of timed events."""

import time

from pynput import keyboard, mouse

from . import events as ev

MOVE_SAMPLE_INTERVAL = 0.015  # seconds; avoids one event per pixel of mouse travel


class Recorder:
    def __init__(self, stop_key=None):
        self.events = []
        self.stop_key = stop_key
        self._start_time = None
        self._last_move_time = 0.0
        self._mouse_listener = None
        self._keyboard_listener = None
        self.recording = False

    def _now(self):
        return time.perf_counter() - self._start_time

    def _on_move(self, x, y):
        if not self.recording:
            return
        now = self._now()
        if now - self._last_move_time < MOVE_SAMPLE_INTERVAL:
            return
        self._last_move_time = now
        self.events.append({"t": now, "type": "move", "x": x, "y": y})

    def _on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        self.events.append(
            {
                "t": self._now(),
                "type": "click",
                "x": x,
                "y": y,
                "button": ev.button_to_str(button),
                "pressed": pressed,
            }
        )

    def _on_scroll(self, x, y, dx, dy):
        if not self.recording:
            return
        self.events.append(
            {"t": self._now(), "type": "scroll", "x": x, "y": y, "dx": dx, "dy": dy}
        )

    def _on_key_down(self, key):
        if not self.recording or key == self.stop_key:
            return
        self.events.append({"t": self._now(), "type": "key_down", "key": ev.key_to_str(key)})

    def _on_key_up(self, key):
        if not self.recording or key == self.stop_key:
            return
        self.events.append({"t": self._now(), "type": "key_up", "key": ev.key_to_str(key)})

    def start(self):
        self.events = []
        self._start_time = time.perf_counter()
        self._last_move_time = 0.0
        self.recording = True
        self._mouse_listener = mouse.Listener(
            on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_down, on_release=self._on_key_up
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self):
        self.recording = False
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        return self.events
