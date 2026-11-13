from clicknick_app.player import evaluate
from clicknick_app.variables import VariableStore


class FakeCtx:
    def __init__(self):
        self.variables = VariableStore()


def test_variable_equals_true():
    ctx = FakeCtx()
    ctx.variables.set("a", "1")
    assert evaluate({"kind": "variable_equals", "name": "a", "value": "1"}, ctx) is True


def test_variable_equals_false():
    ctx = FakeCtx()
    ctx.variables.set("a", "1")
    assert evaluate({"kind": "variable_equals", "name": "a", "value": "2"}, ctx) is False


def test_variable_contains():
    ctx = FakeCtx()
    ctx.variables.set("a", "hello world")
    assert evaluate({"kind": "variable_contains", "name": "a", "value": "wor"}, ctx) is True
    assert evaluate({"kind": "variable_contains", "name": "a", "value": "zzz"}, ctx) is False
