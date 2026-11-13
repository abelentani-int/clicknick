"""Minimal ctypes-based Windows clipboard access (text only).

Avoids going through Tkinter, whose Tcl interpreter is not safe to call
from a background thread — commands run on the player's worker thread.
"""

import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.restype = ctypes.c_void_p
user32.GetClipboardData.restype = wintypes.HANDLE


def set_text(text):
    data = (text + "\0").encode("utf-16-le")
    user32.OpenClipboard(0)
    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        ptr = kernel32.GlobalLock(handle)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        user32.SetClipboardData(CF_UNICODETEXT, handle)
    finally:
        user32.CloseClipboard()


def get_text():
    user32.OpenClipboard(0)
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        ptr = kernel32.GlobalLock(handle)
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
