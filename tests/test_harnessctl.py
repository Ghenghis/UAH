import json
import subprocess
import sys
from pathlib import Path

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
