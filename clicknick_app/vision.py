"""Finds a previously captured reference image on the current screen.

Used by the click_image / wait_image / find_image commands. Matching is a
plain normalized template match — good enough for static UI elements, not a
general computer-vision engine.
"""

import time

import cv2
import numpy as np
from PIL import ImageGrab

DEFAULT_CONFIDENCE = 0.85


def _grab_bgr():
    img = ImageGrab.grab()
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def grab_region(bbox):
    """bbox = (left, top, right, bottom) in screen coordinates."""
    return ImageGrab.grab(bbox=bbox)


def find_on_screen(image_path, confidence=DEFAULT_CONFIDENCE):
    """Returns (center_x, center_y, width, height) of the best match, or
    None if nothing scored above the confidence threshold."""
    template = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Reference image not found: {image_path}")
    screen = _grab_bgr()
    th, tw = template.shape[:2]
    if th > screen.shape[0] or tw > screen.shape[1]:
        return None
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < confidence:
        return None
    x, y = max_loc
    return (x + tw // 2, y + th // 2, tw, th)


def wait_for_image(image_path, timeout=10.0, confidence=DEFAULT_CONFIDENCE, poll_interval=0.3, stop_flag=None):
    """Polls until the image appears or timeout elapses. Returns the match
    tuple from find_on_screen, or None on timeout/stop."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stop_flag is not None and stop_flag.is_set():
            return None
        match = find_on_screen(image_path, confidence=confidence)
        if match is not None:
            return match
        if stop_flag is not None:
            stop_flag.wait(poll_interval)
        else:
            time.sleep(poll_interval)
    return None
