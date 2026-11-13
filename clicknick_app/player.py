"""Replays a recorded event list through synthetic mouse/keyboard input."""

import threading
import time

from pynput import keyboard, mouse

from . import events as ev


class Player:
    def __init__(self, on_finished=None):
        self.on_finished = on_finished
        self._stop_flag = threading.Event()
        self._thread = None
        self.playing = False

    def play(self, event_list, speed=1.0, loops=1):
        if self.playing or not event_list:
            return
        self.playing = True
        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._run, args=(event_list, speed, loops), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_flag.set()

    def _run(self, event_list, speed, loops):
        mouse_ctrl = mouse.Controller()
        keyboard_ctrl = keyboard.Controller()
        infinite = loops <= 0
        count = 0
        try:
            while (infinite or count < loops) and not self._stop_flag.is_set():
                self._play_once(event_list, speed, mouse_ctrl, keyboard_ctrl)
                count += 1
        finally:
            self.playing = False
            if self.on_finished is not None:
                self.on_finished()

    def _play_once(self, event_list, speed, mouse_ctrl, keyboard_ctrl):
        playback_start = time.perf_counter()
        for event in event_list:
            if self._stop_flag.is_set():
                return
            target_time = playback_start + event["t"] / speed
            delay = target_time - time.perf_counter()
            if delay > 0:
                self._stop_flag.wait(delay)
                if self._stop_flag.is_set():
                    return
            self._apply(event, mouse_ctrl, keyboard_ctrl)

    def _apply(self, event, mouse_ctrl, keyboard_ctrl):
        t = event["type"]
        if t == "move":
            mouse_ctrl.position = (event["x"], event["y"])
        elif t == "click":
            mouse_ctrl.position = (event["x"], event["y"])
            button = ev.str_to_button(event["button"])
            if event["pressed"]:
                mouse_ctrl.press(button)
            else:
                mouse_ctrl.release(button)
        elif t == "scroll":
            mouse_ctrl.position = (event["x"], event["y"])
            mouse_ctrl.scroll(event["dx"], event["dy"])
        elif t == "key_down":
            keyboard_ctrl.press(ev.str_to_key(event["key"]))
        elif t == "key_up":
            keyboard_ctrl.release(ev.str_to_key(event["key"]))
