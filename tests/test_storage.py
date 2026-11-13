from clicknick_app.storage import load_macro, save_macro


def test_save_and_load_roundtrip(tmp_path):
    events = [{"t": 0.0, "type": "move", "x": 1, "y": 2}]
    path = tmp_path / "sample.macro.json"
    save_macro(events, path)
    assert load_macro(path) == events
