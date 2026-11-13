# ClickNick

A simple, original mouse/keyboard macro recorder and player for Windows, built
with Python and [`pynput`](https://pynput.readthedocs.io/).

Record global mouse movement, clicks, scroll and keyboard input, then replay
the sequence with adjustable speed and looping. Macros are saved as plain
JSON (`*.macro.json`) and can be reloaded later.

This was built from scratch using well-known, generic techniques (global
input hooks + synthetic input playback) — the same general approach used by
most macro recorders — rather than by reverse engineering any specific
commercial product.

## Features

- Record mouse moves, clicks and scroll wheel
- Record keyboard key down/up
- Global hotkeys: `F9` start/stop recording, `F10` start/stop playback
- Adjustable playback speed and loop count (0 = infinite)
- Command list view of the recorded macro, with delete-selected support
- Save / Open macros as JSON

## Requirements

- Python 3.9+
- Windows (uses global input hooks; should also run on macOS/Linux via
  `pynput`, with platform-specific permission prompts)

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

1. Press **Record (F9)** or hit `F9` to start recording. Press `F9` again to stop.
2. Press **Play (F10)** or hit `F10` to replay the recorded macro.
3. Use **File > Save** to store the macro as a `.macro.json` file.

## Packaging a standalone .exe

To let someone run ClickNick on Windows without installing Python:

```powershell
.venv\Scripts\activate
pip install -r requirements-dev.txt
pyinstaller --onefile --windowed --name ClickNick main.py
```

The result is `dist\ClickNick.exe` — a single file with no dependencies.
Zip it (or just copy the `.exe`) and send it over; double-clicking it runs
the app directly.

Since the `.exe` isn't code-signed, Windows SmartScreen or antivirus may show
an "unknown publisher" warning the first time it runs on another machine —
that's expected for an unsigned build, not a sign of a problem. The person
running it can click "More info" > "Run anyway".

## Project layout

```
clicknick_app/
  events.py    # serialization between pynput objects and JSON-safe dicts
  recorder.py  # captures global mouse/keyboard events with timestamps
  player.py    # replays events with speed/loop control on a background thread
  storage.py   # save/load macros as JSON
  app.py       # Tkinter GUI
main.py        # entry point
```
