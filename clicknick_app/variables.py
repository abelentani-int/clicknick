"""A flat string variable store with {name} substitution, used across
type_text / clipboard / open_url / if-condition commands."""

import re

_TOKEN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class VariableStore:
    def __init__(self):
        self._values = {}

    def set(self, name, value):
        self._values[name] = value

    def get(self, name, default=""):
        return self._values.get(name, default)

    def substitute(self, text):
        return _TOKEN.sub(lambda m: self._values.get(m.group(1), m.group(0)), text)
