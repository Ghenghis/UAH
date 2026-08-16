#!/usr/bin/env python3
"""Write .harness/mcp.json for agent runtimes."""

import json
from pathlib import Path

# Catalog of MCPs the harness can enable. Order in `enabled` is preserved.
MCP_CATALOG = {
    "unity": {
        "command": "uvx",
        "args": [
            "--from",
            "git+https://github.com/CoplayDev/unity-mcp.git",
            "unity-mcp",
        ],
        "env_keys": ["UNITY_PROJECT_PATH", "HARNESS_STATE_DIR"],
    },
    "unityctl": {
        "command": "unityctl",
        "args": ["mcp"],
        "env_keys": [],
    },
    "comfyui": {
        "command": "uvx",
        "args": [
            "--from",
            "git+https://github.com/BiodigitalJaz/comfyui-mcp.git",
            "comfyui-mcp",
        ],
        "env_keys": ["COMFYUI_URL"],
    },
}


def write_mcp_config(
    harness_root: Path,
    enabled: list[str],
    project_path: str,
    harness_state_dir: str,
) -> Path:
    """Render .harness/mcp.json with the given enabled MCPs. Returns the path."""
    harness_root = Path(harness_root)
    out = harness_root / "mcp.json"
    servers = {}
    for name in enabled:
        spec = MCP_CATALOG.get(name)
        if not spec:
            continue
        env = {}
        if "UNITY_PROJECT_PATH" in spec["env_keys"]:
            env["UNITY_PROJECT_PATH"] = project_path
        if "HARNESS_STATE_DIR" in spec["env_keys"]:
            env["HARNESS_STATE_DIR"] = harness_state_dir
        if "COMFYUI_URL" in spec["env_keys"]:
            env["COMFYUI_URL"] = "http://127.0.0.1:8188"
        servers[name] = {
            "command": spec["command"],
            "args": list(spec["args"]),
            "env": env,
        }
    out.write_text(json.dumps({"mcpServers": servers}, indent=2) + "\n")
    return out
