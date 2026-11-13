from clicknick_app.variables import VariableStore


def test_substitute_known_variable():
    store = VariableStore()
    store.set("name", "World")
    assert store.substitute("Hello {name}!") == "Hello World!"


def test_substitute_leaves_unknown_token():
    store = VariableStore()
    assert store.substitute("Hello {missing}") == "Hello {missing}"


def test_get_default():
    store = VariableStore()
    assert store.get("absent", "fallback") == "fallback"
