"""Minimal ctypes-based window focusing, no pywin32 dependency."""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def _get_window_title(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def find_window_by_title(title_contains):
    """Returns the hwnd of the first visible top-level window whose title
    contains the given substring (case-insensitive), or None."""
    needle = title_contains.lower()
    match = {"hwnd": None}

    def callback(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _get_window_title(hwnd)
        if needle in title.lower():
            match["hwnd"] = hwnd
            return False
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return match["hwnd"]


def focus_window(title_contains):
    hwnd = find_window_by_title(title_contains)
    if hwnd is None:
        return False
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    return True
