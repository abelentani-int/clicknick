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

- Record mouse moves, clicks, scroll wheel and keyboard input
- Global hotkeys: `F9` start/stop recording, `F10` start/stop playback
- Adjustable playback speed and loop count (0 = infinite)
- Build or edit macros by hand from the sidebar, without recording:
  mouse click, key press, type text, wait, open program, open website,
  focus window, clipboard read/write, variables, comments
- Image recognition commands: click image, wait for image, find image —
  capture a reference region straight from the screen and the player will
  locate it later and act on it
- `Loop` and `If` are containers: they nest their own list of commands
  (shown as expandable branches in the tree), so macros can repeat a block
  or branch on a variable/clipboard value or an on-screen image
- Command tree view of the macro (recorded steps and hand-built blocks
  mixed freely), with delete-selected support
- Save / Open macros as JSON

Select a row before inserting a new command and it's added right after
that row, in the same list. Select a block's "Repeat:"/"Then:"/"Else:"
branch label to insert as the first item inside that block.

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
  events.py        # serialization between pynput objects and JSON-safe dicts
  recorder.py      # captures global mouse/keyboard events into a command list
  commands.py      # describe()/nesting helpers shared by the tree view and player
  player.py        # recursive interpreter: runs flat + loop/if command trees
  variables.py      # {name} substitution and the variable store
  clipboard.py      # ctypes Windows clipboard access (thread-safe, no Tk)
  window_utils.py  # ctypes window focusing by title substring
  vision.py        # screen capture + template matching for image commands
  capture.py       # interactive drag-to-select screen region -> reference PNG
  dialogs.py       # generic "insert command" form builder
  storage.py       # save/load macros as JSON
  app.py           # Tkinter GUI: toolbar, sidebar, command tree
main.py            # entry point
```
