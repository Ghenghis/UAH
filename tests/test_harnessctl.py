import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

HARNESSCTL = Path(__file__).resolve().parent.parent / "scripts" / "harnessctl.py"
SCRIPTS_DIR = str(HARNESSCTL.parent)

sys.path.insert(0, SCRIPTS_DIR)
import harnessctl  # noqa: E402


def run(*args):
    return subprocess.run(
        [sys.executable, str(HARNESSCTL), *args],
        capture_output=True,
        text=True,
    )


def _reload_harnessctl(tmp_path, monkeypatch):
    harness_root = tmp_path / ".harness"
    monkeypatch.setenv("HARNESS_ROOT", str(harness_root))
    importlib.reload(harnessctl)
    return harness_root


def test_status_returns_json_when_no_harness_is_running(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    result = run("status", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["state"] == "stopped"
    assert payload["editor"] is None
    assert payload["mcps"] == {}


def test_start_acquires_lock_and_spawns_children(tmp_path, monkeypatch):
    harness_root = _reload_harnessctl(tmp_path, monkeypatch)

    fake_subprocess = MagicMock()
    fake_subprocess.STDOUT = -2
    fake_subprocess.Popen = MagicMock(return_value=MagicMock(pid=4242))
    monkeypatch.setattr(harnessctl, "subprocess", fake_subprocess)
    monkeypatch.setattr(harnessctl, "supervisor_loop", lambda ev: None)

    result = harnessctl.main(["start"])
    assert result == 0
    assert (harness_root / "lock").exists()
    # Two children spawned: Unity Editor + unity-mcp
    assert fake_subprocess.Popen.call_count == 2
    # Heartbeat files should have been touched
    assert (harness_root / "heartbeat" / "editor").exists()
    assert (harness_root / "heartbeat" / "mcp-unity").exists()


def test_start_writes_mcp_config_with_enabled_list(tmp_path, monkeypatch):
    harness_root = _reload_harnessctl(tmp_path, monkeypatch)
    monkeypatch.setattr(harnessctl, "supervisor_loop", lambda ev: None)

    fake_subprocess = MagicMock()
    fake_subprocess.STDOUT = -2
    fake_subprocess.Popen = MagicMock(return_value=MagicMock(pid=1))
    monkeypatch.setattr(harnessctl, "subprocess", fake_subprocess)

    result = harnessctl.main(["start"])
    assert result == 0
    mcp_json = harness_root / "mcp.json"
    assert mcp_json.exists()
    data = json.loads(mcp_json.read_text())
    assert "unity" in data["mcpServers"]


def test_stop_releases_lock_and_terminates_children(tmp_path, monkeypatch):
    harness_root = _reload_harnessctl(tmp_path, monkeypatch)
    harness_root.mkdir(parents=True)
    (harness_root / "lock").write_text("999")
    pids_path = harness_root / "state" / "pids.json"
    pids_path.parent.mkdir(parents=True)
    pids_path.write_text(json.dumps({"editor_pid": 1234, "mcp_unity_pid": 1235}))

    fake_terminate = MagicMock()
    monkeypatch.setattr(harnessctl, "_terminate", fake_terminate)

    result = harnessctl.main(["stop"])
    assert result == 0
    assert not (harness_root / "lock").exists()
    fake_terminate.assert_any_call(1234)
    fake_terminate.assert_any_call(1235)


def test_restart_delay_uses_exponential_backoff_capped():
    assert harnessctl.restart_delay(1) == 1.0
    assert harnessctl.restart_delay(2) == 2.0
    assert harnessctl.restart_delay(3) == 4.0
    assert harnessctl.restart_delay(4) == 8.0
    assert harnessctl.restart_delay(5) == 16.0
    assert harnessctl.restart_delay(20) == 60.0  # capped


def test_should_restart_stops_after_threshold():
    # 5 fails within 60s → give up
    recent = [time.time() - i for i in range(5)]
    assert harnessctl.should_restart(recent) is False
    # 4 fails within 60s → still retry
    assert harnessctl.should_restart(recent[:4]) is True


def test_doctor_reports_missing_python(tmp_path, monkeypatch, capsys):
    _reload_harnessctl(tmp_path, monkeypatch)

    fake_shutil = MagicMock()
    fake_shutil.which = MagicMock(return_value=None)
    monkeypatch.setattr(harnessctl, "shutil", fake_shutil)

    result = harnessctl.main(["doctor", "--json"])
    assert result == 64
    out, _err = capsys.readouterr()
    payload = json.loads(out)
    assert any(c["name"] == "python" and not c["ok"] for c in payload["checks"])


def test_license_activate_surfaces_personal_tier_message(
    tmp_path, monkeypatch, capsys
):
    _reload_harnessctl(tmp_path, monkeypatch)

    with patch("license_helper.activate", return_value=1) as activate:
        with patch(
            "license_helper.personal_tier_message",
            return_value="Unity Personal = 1 concurrent MCP connection.",
        ):
            result = harnessctl.main(["license", "activate"])

    assert result == 1
    activate.assert_called_once_with(interactive=False, ulf_path=None)
    _out, err = capsys.readouterr()
    assert "Personal" in err or "1 concurrent" in err


def test_build_local_invokes_unity_batchmode(tmp_path, monkeypatch):
    harness_root = _reload_harnessctl(tmp_path, monkeypatch)
    harness_root.mkdir(parents=True, exist_ok=True)
    (harness_root / "lock").write_text("1")

    fake_shutil = MagicMock()
    fake_shutil.which = lambda x: f"C:/fake/{x}.exe"
    monkeypatch.setattr(harnessctl, "shutil", fake_shutil)

    fake_subprocess = MagicMock()
    fake_subprocess.run = MagicMock(
        return_value=MagicMock(returncode=0, stdout="built", stderr="")
    )
    fake_subprocess.STDOUT = -2
    monkeypatch.setattr(harnessctl, "subprocess", fake_subprocess)

    result = harnessctl.main(["build", "--local", "--target", "Windows64"])
    assert result == 0
    args = fake_subprocess.run.call_args[0][0]
    joined = " ".join(args)
    assert "-batchmode" in joined
    assert "-buildTarget" in joined
    assert "Win64" in joined
    assert "--local" not in joined


def test_enable_persists_to_config_json(tmp_path, monkeypatch):
    harness_root = _reload_harnessctl(tmp_path, monkeypatch)
    harness_root.mkdir(parents=True, exist_ok=True)
    result = harnessctl.main(["enable", "comfyui"])
    assert result == 0
    cfg = json.loads((harness_root / "config.json").read_text())
    assert "comfyui" in cfg["enabled"]


def test_disable_removes_from_config_json(tmp_path, monkeypatch):
    harness_root = _reload_harnessctl(tmp_path, monkeypatch)
    harness_root.mkdir(parents=True, exist_ok=True)
    (harness_root / "config.json").write_text(
        json.dumps({"enabled": ["unity", "comfyui"]})
    )
    result = harnessctl.main(["disable", "comfyui"])
    assert result == 0
    cfg = json.loads((harness_root / "config.json").read_text())
    assert "comfyui" not in cfg["enabled"]
