import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mock_unity_bridge import MockUnityBridge  # noqa: E402


def test_mock_bridge_lists_open_scenes():
    bridge = MockUnityBridge()
    bridge.open_scene("Main.unity")
    assert "Main.unity" in bridge.list_open_scenes()


def test_mock_bridge_can_simulate_crash():
    bridge = MockUnityBridge()
    bridge.open_scene("Main.unity")
    bridge.simulate_crash()
    with pytest.raises(RuntimeError):
        bridge.list_open_scenes()


def test_mock_bridge_can_simulate_hang():
    bridge = MockUnityBridge()
    bridge.simulate_hang()
    with pytest.raises(TimeoutError):
        bridge.list_open_scenes(timeout=0.1)


def test_mock_bridge_can_simulate_domain_reload():
    bridge = MockUnityBridge()
    bridge.open_scene("Main.unity")
    bridge.simulate_domain_reload()
    # After reload, the bridge is back up but the scene list is restored.
    assert "Main.unity" in bridge.list_open_scenes()
