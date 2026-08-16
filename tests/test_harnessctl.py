import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

HARNESSCTL = Path(__file__).resolve().parent.parent / "scripts" / "harnessctl.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(HARNESSCTL), *args],
        capture_output=True,
        text=True,
    )


def test_status_returns_json_when_no_harness_is_running(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    result = run("status", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["state"] == "stopped"
    assert payload["editor"] is None
    assert payload["mcps"] == {}


def test_start_acquires_lock_and_spawns_children(tmp_path, monkeypatch):
    harness_root = tmp_path / ".harness"
    monkeypatch.setenv("HARNESS_ROOT", str(harness_root))

    scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
    old_path = sys.path[:]
    sys.path.insert(0, scripts_dir)
    try:
        import harnessctl  # noqa: E402
    finally:
        sys.path[:] = old_path

    fake_subprocess = MagicMock()
    fake_subprocess.STDOUT = -2
    fake_subprocess.Popen = MagicMock(return_value=MagicMock(pid=4242))
    monkeypatch.setattr(harnessctl, "subprocess", fake_subprocess)

    result = harnessctl.main(["start"])
    assert result == 0
    assert (harness_root / "lock").exists()
    # Two children spawned: Unity Editor + unity-mcp
    assert fake_subprocess.Popen.call_count == 2
    # Heartbeat files should have been touched
    assert (harness_root / "heartbeat" / "editor").exists()
    assert (harness_root / "heartbeat" / "mcp-unity").exists()
