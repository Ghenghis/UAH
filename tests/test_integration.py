import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mock_unity_bridge import MockUnityBridge  # noqa: E402
from reconnect import reconnect_to_editor  # noqa: E402


def test_domain_reload_then_probe_succeeds(tmp_path):
    bridge = MockUnityBridge()
    bridge.open_scene("Main.unity")
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    # Simulate a domain reload (briefly unavailable)
    bridge.simulate_domain_reload()
    assert reconnect_to_editor(bridge, state_dir) is True


def test_domain_reload_with_half_dead_bridge_fails(tmp_path):
    bridge = MockUnityBridge()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    bridge.simulate_crash()  # bridge "up" from caller's POV, but actually dead
    assert reconnect_to_editor(bridge, state_dir) is False


def test_editor_hang_is_distinguishable_from_crash(tmp_path):
    bridge = MockUnityBridge()
    bridge.simulate_hang()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    # reconnect treats the probe failure as a failed reconnect, not a crash
    assert reconnect_to_editor(bridge, state_dir) is False
    # but the bridge did not actually crash
    bridge.recover_from_crash()
    assert reconnect_to_editor(bridge, state_dir) is True
