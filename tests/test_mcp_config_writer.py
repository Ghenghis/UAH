import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from mcp_config_writer import write_mcp_config  # noqa: E402


def test_writes_enabled_mcps(tmp_path):
    out = write_mcp_config(
        harness_root=tmp_path,
        enabled=["unity"],
        project_path="C:/projects/foo",
        harness_state_dir="C:/projects/foo/.harness/state",
    )
    data = json.loads(out.read_text())
    assert "mcpServers" in data
    assert "unity" in data["mcpServers"]
    entry = data["mcpServers"]["unity"]
    assert entry["command"] == "uvx"
    assert "CoplayDev/unity-mcp" in " ".join(entry["args"])
    assert entry["env"]["UNITY_PROJECT_PATH"] == "C:/projects/foo"
    assert entry["env"]["HARNESS_STATE_DIR"] == "C:/projects/foo/.harness/state"


def test_omits_disabled_mcps(tmp_path):
    out = write_mcp_config(
        harness_root=tmp_path,
        enabled=[],
        project_path="x",
        harness_state_dir="y",
    )
    data = json.loads(out.read_text())
    assert data["mcpServers"] == {}
