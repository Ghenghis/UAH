import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from reconnect import reconnect_to_editor  # noqa: E402


def test_reconnect_success_on_healthy_bridge(tmp_path):
    bridge = MagicMock()
    bridge.list_open_scenes.return_value = ["Main.unity"]
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    assert reconnect_to_editor(bridge, state_dir) is True
    bridge.list_open_scenes.assert_called_once()


def test_reconnect_failure_when_probe_fails(tmp_path):
    bridge = MagicMock()
    bridge.list_open_scenes.side_effect = RuntimeError("bridge dead")
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    assert reconnect_to_editor(bridge, state_dir) is False
