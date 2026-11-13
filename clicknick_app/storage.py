"""Save and load recorded macros as JSON (.macro) files."""

import json

FORMAT_VERSION = 1


def save_macro(event_list, path):
    payload = {"version": FORMAT_VERSION, "events": event_list}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_macro(path):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload["events"]
