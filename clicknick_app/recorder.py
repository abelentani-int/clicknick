"""Captures global mouse and keyboard activity into a flat list of commands.

Each recorded command carries a "delay": seconds to wait after the previous
command finished before this one runs. This is the same field manually
inserted commands use, so recorded and hand-built steps mix freely.
"""

import time

from pynput import keyboard, mouse

from . import events as ev

MOVE_SAMPLE_INTERVAL = 0.015  # seconds; avoids one event per pixel of mouse travel


class Recorder:
    def __init__(self, stop_key=None):
        self.events = []
        self.stop_key = stop_key
        self._last_event_time = None
        self._last_move_time = None
        self._mouse_listener = None
        self._keyboard_listener = None
        self.recording = False

    def _delay(self):
        now = time.perf_counter()
        delay = 0.0 if self._last_event_time is None else now - self._last_event_time
        self._last_event_time = now
        return delay

    def _on_move(self, x, y):
        if not self.recording:
            return
        now = time.perf_counter()
        if self._last_move_time is not None and now - self._last_move_time < MOVE_SAMPLE_INTERVAL:
            return
        self._last_move_time = now
        self.events.append({"type": "move", "x": x, "y": y, "delay": self._delay()})

    def _on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        self.events.append(
            {
                "type": "click",
                "x": x,
                "y": y,
                "button": ev.button_to_str(button),
                "pressed": pressed,
                "delay": self._delay(),
            }
        )

    def _on_scroll(self, x, y, dx, dy):
        if not self.recording:
            return
        self.events.append(
            {"type": "scroll", "x": x, "y": y, "dx": dx, "dy": dy, "delay": self._delay()}
        )

    def _on_key_down(self, key):
        if not self.recording or key == self.stop_key:
            return
        self.events.append({"type": "key_down", "key": ev.key_to_str(key), "delay": self._delay()})

    def _on_key_up(self, key):
        if not self.recording or key == self.stop_key:
            return
        self.events.append({"type": "key_up", "key": ev.key_to_str(key), "delay": self._delay()})

    def start(self):
        self.events = []
        self._last_event_time = None
        self._last_move_time = None
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
