import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from file_ipc import StateStore, StateCorruptError  # noqa: E402


def test_write_and_read(tmp_path):
    store = StateStore(tmp_path)
    store.write("scene.json", {"last_selected": "Cube"})
    assert store.read("scene.json") == {"last_selected": "Cube"}


def test_quarantine_on_corrupt_json(tmp_path):
    store = StateStore(tmp_path)
    (tmp_path / "scene.json").write_text("{not json")
    try:
        store.read("scene.json")
    except StateCorruptError:
        pass
    else:
        raise AssertionError("expected StateCorruptError")
    files = list((tmp_path / "quarantine").iterdir())
    assert len(files) == 1
    assert files[0].name.endswith("-scene.json")


def test_stale_state_detected(tmp_path):
    store = StateStore(tmp_path, stale_seconds=1)
    (tmp_path / "scene.json").write_text(json.dumps({"a": 1}))
    time.sleep(2)
    assert store.is_stale("scene.json") is True
