from clicknick_app import commands


def test_describe_wait():
    assert commands.describe({"type": "wait", "delay": 1.5}) == "Wait 1.50s"


def test_describe_loop_infinite():
    assert commands.describe({"type": "loop", "count": 0}) == "Loop (infinite)"


def test_describe_loop_finite():
    assert commands.describe({"type": "loop", "count": 3}) == "Loop (3x)"


def test_describe_if():
    cmd = {"type": "if", "condition": {"kind": "variable_equals", "name": "a", "value": "x"}}
    assert commands.describe(cmd) == 'If a == "x"'


def test_loop_children_creates_list_once():
    cmd = {"type": "loop", "count": 1}
    children = commands.loop_children(cmd)
    assert children == []
    assert cmd["children"] is children


def test_then_else_children_are_independent():
    cmd = {"type": "if", "condition": {"kind": "variable_equals", "name": "a", "value": "x"}}
    then_list = commands.then_children(cmd)
    else_list = commands.else_children(cmd)
    assert then_list == [] and else_list == []
    assert then_list is not else_list
