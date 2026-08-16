# Unity AI Harness — Local Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-hosted Unity AI development harness for Windows 11 — `harnessctl` supervisor + file-IPC state layer + license helper + cost meter, with CoplayDev/unity-mcp as the primary MCP bridge. The first vertical slice delivers `harnessctl start` + primary MCP + domain-reload survival; everything else supports that.

**Architecture:** Native Windows processes supervised by a small Python CLI. No Docker. The Editor + MCP servers live as long-lived children of `harnessctl`; file-IPC in `.harness/state/` is the durable boundary that survives Unity domain reloads. GameCI is invoked only for builds.

**Tech Stack:** Python 3.11+ (stdlib + `psutil`, `pyyaml`, `pytest`), Bash 4+ (Git Bash on Windows), Git submodules, Unity 2022.3 LTS or Unity 6.x, CoplayDev/unity-mcp, game-ci/cli, `butterlatte-zhang/unity-ai-bridge` as a reference (not vendored).

**Spec:** [`../specs/2026-08-15-unity-ai-harness-local-design.md`](../specs/2026-08-15-unity-ai-harness-local-design.md)
**Vision:** [`../../../VISION.md`](../../../VISION.md)

> **Note on worktrees:** This plan would normally run in an isolated worktree. The harness repo is not currently a git repo, so worktrees are skipped. Once the repo is initialized (`git init`), future revisions of this plan should add worktree isolation.

---

## File Structure

### Create

| Path | Responsibility | Approx LoC |
|---|---|---|
| `scripts/harnessctl.py` | Supervisor CLI: start / stop / status / restart / build / license / doctor / setup / enable / disable | 300 |
| `scripts/file_ipc.py` | JSON sidecar layer in `.harness/state/`; survives domain reloads | 150 |
| `scripts/mcp_config_writer.py` | Writes `.harness/mcp.json` deterministically | 60 |
| `scripts/license_helper.py` | Wraps `game-ci/unity-license-activate` | 100 |
| `scripts/cost_meter.py` | Daemon that tails agent-runtime output and logs token spend | 80 |
| `scripts/setup.sh` | Idempotent one-time install (Phase 0.5) | 100 |
| `scripts/mirror-to-gitlab.sh` | Mirror to GitLab remote after `git push` | 30 |
| `tests/test_harnessctl.py` | Supervisor state machine, lock-file races | 200 |
| `tests/test_file_ipc.py` | Round-trip, quarantine, rotation | 150 |
| `tests/test_mcp_config_writer.py` | Deterministic JSON output | 80 |
| `tests/test_license_helper.py` | Argument parsing + exit codes | 80 |
| `tests/test_cost_meter.py` | Per-runtime format parsers | 120 |
| `tests/mock_unity_bridge.py` | Fake Unity that accepts MCP protocol; simulates crash/hang/domain-reload | 180 |
| `tests/test_integration.py` | End-to-end with mock Unity: domain reload, MCP crash, Editor hang, license cap | 250 |
| `configs/env.example` | `KENNEY_ASSETS_PATH`, `OPENCODEX_PORT`, `HARNESS_ROOT` | 20 |
| `docs/TESTING.md` | Manual scenarios that need a real Editor | 80 |
| `.gitignore` | Top-level ignore (Library/, Temp/, Build/, .harness/state/heartbeat/logs/cost.log/build.log/lock/quarantine, *.ulf) | 25 |
| `.gitmodules` | Submodule pins: unity-mcp, game-ci, unity-ai-bridge (reference), unityctl (optional), comfyui-mcp (optional) | 20 |

### Modify

| Path | Change |
|---|---|
| `docs/03-ACTION-PLAN.md` | Already updated; tighten later if needed |
| `docs/04-MCP-AND-CLI-NOTES.md` | Already updated |
| `README.md` | Already updated |
| `VISION.md` | Already created |
| `examples/PROJECT-STATUS.template.md` | Add fields the harness writes (last build, total tokens, last tool) |

---

## Milestones

**M1 — First vertical slice (Tasks 1–9):** `harnessctl start` brings up Unity + primary MCP; file-IPC survives a domain reload; `.harness/mcp.json` is written. **This is the slice that proves the architecture.**

**M2 — Operator ergonomics (Tasks 10–13):** `doctor`, `license`, `cost meter`, `build --local`, GitLab mirror. Daily-use surface.

**M3 — Optional surfaces (Tasks 14–15):** `enable comfyui`, `enable unityctl`.

**M4 — Integration tests + manual test doc (Tasks 16–17):** Mock Unity bridge; end-to-end coverage of error scenarios; manual test runbook.

---

## Phase 0 — Foundation

### Task 1: Initialize repo, submodules, env, .gitignore

**Files:**
- Create: `.gitignore`, `.gitmodules`, `configs/env.example`

- [ ] **Step 1: Initialize git repo**

```bash
cd G:/Github/unity-ai-harness
git init
git config user.email "harness@local"
git config user.name "harness"
```

Expected: `Initialized empty Git repository in .../.git/`

- [ ] **Step 2: Add submodules (idempotent — safe to re-run)**

```bash
git submodule add https://github.com/CoplayDev/unity-mcp.git tools/unity-mcp
git submodule add https://github.com/game-ci/cli.git tools/game-ci
git submodule add https://github.com/butterlatte-zhang/unity-ai-bridge.git tools/unity-ai-bridge-reference
```

Expected: three entries in `.gitmodules`. If `tools/unity-mcp` etc. already exist, the command updates them.

- [ ] **Step 3: Write `.gitignore`**

```gitignore
# Unity
[Ll]ibrary/
[Tt]emp/
[Oo]bj/
[Bb]uild/
[Bb]uilds/
[Ll]ogs/
[Uu]ser[Ss]ettings/
[Mm]emoryCaptures/
[Rr]ecordings/

# Harness runtime state (regenerated)
.harness/state/
.harness/heartbeat/
.harness/logs/
.harness/cost.log
.harness/build.log
.harness/lock
.harness/quarantine/

# Editor backups
*~
*.swp
.vscode/
.idea/

# License files
*.ulf
*.ulf.*

# Python
__pycache__/
*.pyc
.pytest_cache/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 4: Write `configs/env.example`**

```bash
# Unity AI Harness — environment template
# Copy to .env (gitignored) and edit.

# Required: absolute path to your asset pack. The setup script symlinks this
# into <project>/Assets/_Imported/.
KENNEY_ASSETS_PATH=G:\Github\Kenney Game Assets All-in-1 3.6.0

# Optional: Unity install path (defaults to Unity Hub default on Windows).
UNITY_HUB_PATH=C:\Program Files\Unity\Hub\Editor

# Optional: Unity CLI override (defaults to <UNITY_HUB_PATH>/<version>/Editor/Unity.exe).
UNITY_CLI=

# Optional: OpenCodex proxy port (defaults to 10100).
OPENCODEX_PORT=10100

# Optional: harness state dir override (defaults to <project>/.harness).
# HARNESS_ROOT=
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore .gitmodules configs/env.example
git commit -m "chore: init repo, submodules, env template, gitignore"
```

---

### Task 2: Setup script (Phase 0.5 idempotent install)

**Files:**
- Create: `scripts/setup.sh`
- Create: `tests/test_setup_script.sh` (smoke test using a temp project)

- [ ] **Step 1: Write the failing smoke test**

```bash
#!/usr/bin/env bash
# tests/test_setup_script.sh — verifies setup.sh validates preconditions
set -euo pipefail

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

# Mock environment
export KENNEY_ASSETS_PATH="$TMP/fake-kenny"
mkdir -p "$KENNEY_ASSETS_PATH"

# Run setup.sh against an empty project; it should succeed and create the symlink
bash scripts/setup.sh "$TMP/test-project" 2>&1 | tee "$TMP/out.log"

# Verify symlink was created
test -L "$TMP/test-project/Assets/_Imported"

# Verify PROJECT-STATUS.md was written
test -f "$TMP/test-project/PROJECT-STATUS.md"

# Re-run; must be idempotent
bash scripts/setup.sh "$TMP/test-project" >/dev/null 2>&1
echo "OK: setup.sh idempotent"
```

- [ ] **Step 2: Run the smoke test (should fail)**

```bash
bash tests/test_setup_script.sh
```

Expected: failure because `scripts/setup.sh` does not exist yet.

- [ ] **Step 3: Write `scripts/setup.sh`**

```bash
#!/usr/bin/env bash
# scripts/setup.sh — Phase 0.5 idempotent install for the Unity AI Harness.
#
# Usage: bash scripts/setup.sh [project_dir]
#   project_dir: optional; defaults to the current directory.
#
# Env:
#   KENNEY_ASSETS_PATH  required (path to asset pack; will be symlinked)
#   UNITY_HUB_PATH      optional
#
# Idempotent: re-running is safe and a no-op if everything is already set up.

set -euo pipefail

PROJECT_DIR="${1:-$PWD}"
KENNEY_ASSETS_PATH="${KENNEY_ASSETS_PATH:-}"

# --- 1. Preconditions -------------------------------------------------------
if [[ -z "$KENNEY_ASSETS_PATH" ]]; then
    echo "ERROR: KENNEY_ASSETS_PATH is not set." >&2
    echo "  Set it to the absolute path of your asset pack, e.g." >&2
    echo "    export KENNEY_ASSETS_PATH='G:\\Github\\Kenney Game Assets All-in-1 3.6.0'" >&2
    exit 64  # EX_USAGE
fi
if [[ ! -d "$KENNEY_ASSETS_PATH" ]]; then
    echo "ERROR: KENNEY_ASSETS_PATH='$KENNEY_ASSETS_PATH' is not a directory." >&2
    exit 64
fi
if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git not on PATH." >&2
    exit 69  # EX_UNAVAILABLE
fi
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: python not on PATH (need 3.11+)." >&2
    exit 69
fi

# --- 2. Submodules ----------------------------------------------------------
cd "$(dirname "$0")/.."
git submodule update --init --recursive

# --- 3. Project directory ---------------------------------------------------
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
mkdir -p Assets Packages ProjectSettings .harness/state .harness/heartbeat \
         .harness/logs .harness/quarantine

# --- 4. Symlink Kenny -------------------------------------------------------
if [[ ! -L Assets/_Imported ]]; then
    ln -s "$KENNEY_ASSETS_PATH" Assets/_Imported
    echo "Created symlink: Assets/_Imported -> $KENNEY_ASSETS_PATH"
else
    echo "Symlink already exists: Assets/_Imported"
fi

# --- 5. UPM manifest entry (only if not present) ----------------------------
if [[ ! -f Packages/manifest.json ]]; then
    cat > Packages/manifest.json <<'JSON'
{
  "dependencies": {
    "com.unity-mcp": "https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity"
  }
}
JSON
    echo "Wrote Packages/manifest.json"
fi

# --- 6. PROJECT-STATUS.md --------------------------------------------------
if [[ ! -f PROJECT-STATUS.md ]]; then
    cp "$(dirname "$0")/../examples/PROJECT-STATUS.template.md" PROJECT-STATUS.md
    echo "Wrote PROJECT-STATUS.md"
fi

# --- 7. License activation (best-effort, non-fatal) ------------------------
if python scripts/harnessctl.py license status >/dev/null 2>&1; then
    echo "License: already activated"
else
    echo "License: not activated. Run 'harnessctl license activate' when ready."
fi

echo "Setup complete. Next: 'harnessctl start'."
```

- [ ] **Step 4: Run the smoke test (should pass)**

```bash
chmod +x scripts/setup.sh
bash tests/test_setup_script.sh
```

Expected: `OK: setup.sh idempotent`

- [ ] **Step 5: Commit**

```bash
git add scripts/setup.sh tests/test_setup_script.sh
git commit -m "feat(setup): idempotent Phase 0.5 install"
```

---

## Phase 1 — First vertical slice (M1)

### Task 3: `harnessctl` skeleton + `status` command

**Files:**
- Create: `scripts/harnessctl.py`
- Test: `tests/test_harnessctl.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_harnessctl.py
import json
import subprocess
import sys
from pathlib import Path

HARNESSCTL = Path(__file__).resolve().parent.parent / "scripts" / "harnessctl.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(HARNESSCTL), *args],
        capture_output=True, text=True,
    )


def test_status_returns_json_when_no_harness_is_running(tmp_path, monkeypatch):
    # Use a temp project dir so we don't touch the real .harness
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    result = run("--json", "status")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["state"] == "stopped"
    assert payload["editor"] is None
    assert payload["mcps"] == {}
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_harnessctl.py::test_status_returns_json_when_no_harness_is_running -v
```

Expected: collection error or FAIL because `scripts/harnessctl.py` does not exist.

- [ ] **Step 3: Write `scripts/harnessctl.py` (skeleton + status)**

```python
#!/usr/bin/env python3
# scripts/harnessctl.py — Unity AI Harness supervisor.
#
# Subcommands: start | stop | status | restart | build | license | doctor |
#              setup | enable | disable
#
# All output is human-friendly by default; pass --json for machine-readable.

import argparse
import json
import os
import sys
from pathlib import Path

HARNESS_ROOT = Path(os.environ.get("HARNESS_ROOT", Path.cwd() / ".harness"))
LOCK_FILE = HARNESS_ROOT / "lock"
STATE_DIR = HARNESS_ROOT / "state"
CONFIG_FILE = HARNESS_ROOT / "config.json"


def status_payload() -> dict:
    """Return the canonical harness state. Read-only."""
    running = LOCK_FILE.exists() and (LOCK_FILE.stat().st_mtime
                                      > (now() - 300))  # 5 min
    return {
        "state": "running" if running else "stopped",
        "harness_root": str(HARNESS_ROOT),
        "editor": None,         # filled by start/stop; nil when stopped
        "mcps": {},             # filled by start/stop; {} when stopped
    }


def now() -> float:
    import time
    return time.time()


def cmd_status(args) -> int:
    payload = status_payload()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        s = payload["state"]
        print(f"Harness: {s}")
        print(f"Root:    {payload['harness_root']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harnessctl")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("start").add_argument("--json", action="store_true")
    stop = sub.add_parser("stop")
    stop.add_argument("--json", action="store_true")
    sub_status = sub.add_parser("status")
    sub_status.add_argument("--json", action="store_true")
    sub.add_parser("restart").add_argument("--json", action="store_true")
    sub.add_parser("build").add_argument("--target", default="Windows64")
    sub.add_parser("build").add_argument("--local", action="store_true")
    sub.add_parser("doctor").add_argument("--json", action="store_true")
    sub.add_parser("setup")
    sub.add_parser("enable").add_argument("name")
    sub.add_parser("disable").add_argument("name")
    sub.add_parser("license").add_argument("subcmd", nargs="?")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "status":
        return cmd_status(args)
    print(f"(stub) {args.cmd} not implemented yet", file=sys.stderr)
    return 78  # EX_CONFIG


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_harnessctl.py::test_status_returns_json_when_no_harness_is_running -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/harnessctl.py tests/test_harnessctl.py
git commit -m "feat(harnessctl): skeleton with status command"
```

---

### Task 4: `harnessctl start` — bring up Editor + primary MCP

**Files:**
- Create: `scripts/harnessctl.py` (extend)
- Test: `tests/test_harnessctl.py` (extend)

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_harnessctl.py
import os
from unittest.mock import patch, MagicMock


def test_start_acquires_lock_and_spawns_children(tmp_path, monkeypatch):
    harness_root = tmp_path / ".harness"
    monkeypatch.setenv("HARNESS_ROOT", str(harness_root))

    fake_popen = MagicMock()
    fake_popen.pid = 4242
    with patch("subprocess.Popen", return_value=fake_popen) as popen:
        result = run("start")
    assert result.returncode == 0
    assert (harness_root / "lock").exists()
    # Two children spawned: Unity Editor + unity-mcp
    assert popen.call_count == 2
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_harnessctl.py::test_start_acquires_lock_and_spawns_children -v
```

Expected: FAIL — `start` is currently a stub.

- [ ] **Step 3: Extend `scripts/harnessctl.py`**

Add this near the top, after imports:

```python
import subprocess
import time

EDITOR_CMD = ["unity", "-projectPath", "."]   # Unity CLI invocation
PRIMARY_MCP_CMD = [
    "uvx", "--from", "git+https://github.com/CoplayDev/unity-mcp.git", "unity-mcp"
]
```

Add this `cmd_start` function and update `main`:

```python
def _acquire_lock() -> bool:
    """Return True if we acquired the lock; False if another harnessctl holds it."""
    HARNESS_ROOT.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists() and (LOCK_FILE.stat().st_mtime > (now() - 300)):
        return False
    LOCK_FILE.write_text(str(os.getpid()))
    return True


def _release_lock() -> None:
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def _spawn(cmd: list[str], log_name: str) -> subprocess.Popen:
    log_path = HARNESS_ROOT / "logs" / f"{log_name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = open(log_path, "ab")
    return subprocess.Popen(
        cmd, stdout=log, stderr=subprocess.STDOUT,
        cwd=os.getcwd(),
    )


def cmd_start(args) -> int:
    if not _acquire_lock():
        print("Another harnessctl is running.", file=sys.stderr)
        return 75  # EX_TEMPFAIL
    try:
        editor = _spawn(EDITOR_CMD, "editor")
        mcp = _spawn(PRIMARY_MCP_CMD, "mcp-unity")
        (HARNESS_ROOT / "state" / "pids.json").write_text(json.dumps({
            "editor_pid": editor.pid,
            "mcp_unity_pid": mcp.pid,
        }))
        # Best-effort: regenerate mcp.json for agent runtimes to discover
        try:
            from mcp_config_writer import write_mcp_config
            write_mcp_config(HARNESS_ROOT, enabled=["unity"])
        except Exception as e:  # non-fatal; doctor will surface
            (HARNESS_ROOT / "logs" / "mcp-config-writer.log").write_text(
                f"{time.time()}: mcp.json write failed: {e}\n")
        print(f"Editor pid={editor.pid}, MCP pid={mcp.pid}")
        return 0
    except Exception:
        _release_lock()
        raise
```

Update `main` so the `start` branch calls `cmd_start`:

```python
def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "start":
        return cmd_start(args)
    print(f"(stub) {args.cmd} not implemented yet", file=sys.stderr)
    return 78
```

Also extend `status_payload` to read the pids when running:

```python
def status_payload() -> dict:
    running = LOCK_FILE.exists() and (LOCK_FILE.stat().st_mtime > (now() - 300))
    payload = {
        "state": "running" if running else "stopped",
        "harness_root": str(HARNESS_ROOT),
        "editor": None,
        "mcps": {},
    }
    if running:
        pids_path = STATE_DIR / "pids.json"
        if pids_path.exists():
            pids = json.loads(pids_path.read_text())
            payload["editor"] = {"pid": pids.get("editor_pid")}
            payload["mcps"]["unity"] = {"pid": pids.get("mcp_unity_pid")}
    return payload
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_harnessctl.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/harnessctl.py tests/test_harnessctl.py
git commit -m "feat(harnessctl): start spawns editor + primary MCP, acquires lock"
```

---

### Task 5: `mcp_config_writer` — deterministic `.harness/mcp.json`

**Files:**
- Create: `scripts/mcp_config_writer.py`
- Test: `tests/test_mcp_config_writer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mcp_config_writer.py
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
        harness_root=tmp_path, enabled=[],
        project_path="x", harness_state_dir="y",
    )
    data = json.loads(out.read_text())
    assert data["mcpServers"] == {}
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_mcp_config_writer.py -v
```

Expected: ImportError because `mcp_config_writer.py` does not exist.

- [ ] **Step 3: Write `scripts/mcp_config_writer.py`**

```python
# scripts/mcp_config_writer.py — writes .harness/mcp.json for agent runtimes.

import json
from pathlib import Path

# Catalog of MCPs the harness can enable. Order in `enabled` is preserved.
MCP_CATALOG = {
    "unity": {
        "command": "uvx",
        "args": ["--from",
                 "git+https://github.com/CoplayDev/unity-mcp.git",
                 "unity-mcp"],
        "env_keys": ["UNITY_PROJECT_PATH", "HARNESS_STATE_DIR"],
    },
    "unityctl": {
        "command": "unityctl",
        "args": ["mcp"],
        "env_keys": [],
    },
    "comfyui": {
        "command": "uvx",
        "args": ["--from",
                 "git+https://github.com/BiodigitalJaz/comfyui-mcp.git",
                 "comfyui-mcp"],
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
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_mcp_config_writer.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/mcp_config_writer.py tests/test_mcp_config_writer.py
git commit -m "feat(harnessctl): deterministic .harness/mcp.json writer"
```

---

### Task 6: file-IPC layer — round-trip + quarantine

**Files:**
- Create: `scripts/file_ipc.py`
- Test: `tests/test_file_ipc.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_file_ipc.py
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
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_file_ipc.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `scripts/file_ipc.py`**

```python
# scripts/file_ipc.py — durable sidecar state for surviving Unity domain reloads.
#
# Inspired by butterlatte-zhang/unity-ai-bridge's file-IPC pattern. The actual
# implementation here is written from scratch and tuned to the harness's needs.

import json
import shutil
import time
from pathlib import Path


class StateCorruptError(Exception):
    """Raised when a state file cannot be parsed. File is auto-quarantined."""


class StateStore:
    def __init__(self, state_dir: Path, stale_seconds: int = 300):
        self.state_dir = Path(state_dir)
        self.quarantine_dir = self.state_dir / "quarantine"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.stale_seconds = stale_seconds

    def write(self, name: str, payload: dict) -> Path:
        path = self.state_dir / name
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(path)
        return path

    def read(self, name: str) -> dict:
        path = self.state_dir / name
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as e:
            self._quarantine(path)
            raise StateCorruptError(str(e)) from e

    def is_stale(self, name: str) -> bool:
        path = self.state_dir / name
        if not path.exists():
            return True
        age = time.time() - path.stat().st_mtime
        return age > self.stale_seconds

    def _quarantine(self, path: Path) -> None:
        ts = int(time.time())
        dest = self.quarantine_dir / f"{ts}-{path.name}"
        shutil.move(str(path), str(dest))
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_file_ipc.py -v
```

Expected: all three tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/file_ipc.py tests/test_file_ipc.py
git commit -m "feat(harnessctl): file-IPC state layer with quarantine"
```

---

### Task 7: Domain-reload survival — heartbeat + reconnect probe

**Files:**
- Create: `scripts/heartbeat.py`
- Test: `tests/test_heartbeat.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_heartbeat.py
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from heartbeat import Heartbeat, HeartbeatMissing  # noqa: E402


def test_heartbeat_written_and_checked(tmp_path):
    hb_dir = tmp_path / "heartbeat"
    hb = Heartbeat(hb_dir, name="editor", interval=0.05)
    hb.start()
    time.sleep(0.1)
    assert hb.is_alive(max_age=1.0) is True
    hb.stop()


def test_missing_heartbeat_detected(tmp_path):
    hb = Heartbeat(tmp_path / "heartbeat", name="editor")
    try:
        hb.is_alive(max_age=0.1)
    except HeartbeatMissing:
        pass
    else:
        raise AssertionError("expected HeartbeatMissing")
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_heartbeat.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `scripts/heartbeat.py`**

```python
# scripts/heartbeat.py — per-process heartbeat files used to detect crashes/hangs.

import threading
import time
from pathlib import Path


class HeartbeatMissing(Exception):
    pass


class Heartbeat:
    def __init__(self, hb_dir: Path, name: str, interval: float = 2.0):
        self.path = Path(hb_dir) / name
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._touch()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 2)
        if self.path.exists():
            self.path.unlink()

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            self._touch()

    def _touch(self) -> None:
        self.path.write_text(str(time.time()))

    def is_alive(self, max_age: float = 10.0) -> bool:
        if not self.path.exists():
            raise HeartbeatMissing(str(self.path))
        age = time.time() - self.path.stat().st_mtime
        if age > max_age:
            raise HeartbeatMissing(f"stale by {age:.1f}s")
        return True
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_heartbeat.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Add heartbeat hook to `harnessctl start`**

Update `cmd_start` in `scripts/harnessctl.py` to also start heartbeats for the Editor and the MCP. Insert just before the `print(...)` line:

```python
    from heartbeat import Heartbeat
    Heartbeat(HARNESS_ROOT / "heartbeat", "editor", interval=2.0).start()
    Heartbeat(HARNESS_ROOT / "heartbeat", "mcp-unity", interval=2.0).start()
```

These heartbeats run in daemon threads; they die when the parent Python process exits. (Phase 2 will introduce a long-lived supervisor process; for now this is enough for the vertical slice.)

- [ ] **Step 6: Add a test that verifies the heartbeat files appear after start**

Append to `tests/test_harnessctl.py`:

```python
def test_start_creates_heartbeat_files(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    with patch("subprocess.Popen", return_value=MagicMock(pid=1)):
        run("start")
    hb = tmp_path / ".harness" / "heartbeat"
    assert (hb / "editor").exists()
    assert (hb / "mcp-unity").exists()
```

- [ ] **Step 7: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/harnessctl.py scripts/heartbeat.py tests/test_harnessctl.py tests/test_heartbeat.py
git commit -m "feat(harnessctl): heartbeats for editor + primary MCP"
```

---

### Task 8: Domain-reload recovery — reconnect + post-reconnect health probe

**Files:**
- Create: `scripts/reconnect.py`
- Test: `tests/test_reconnect.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reconnect.py
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
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_reconnect.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `scripts/reconnect.py`**

```python
# scripts/reconnect.py — domain-reload recovery for the primary Unity MCP.
#
# Sequence after the Editor finishes a domain reload:
#   1. Reconnect the WebSocket / named pipe.
#   2. Read .harness/state/ sidecars to restore agent-visible context.
#   3. Issue one lightweight tool call (post-reconnect health probe).
#   4. If the probe fails, return False so the caller treats it as a fresh
#      MCP crash (harnessctl will auto-restart with exponential backoff).
#
# The bridge argument is the MCP's connection object — anything with the
# .list_open_scenes() method, so this is mockable without Unity.

from file_ipc import StateStore


def reconnect_to_editor(bridge, state_dir: Path) -> bool:
    """Restore agent-visible state and probe the Editor. Returns True on success."""
    store = StateStore(state_dir)
    try:
        # Step 1+2: read sidecars (best-effort; corruption already handled by store)
        try:
            store.read("scene.json")
        except Exception:
            pass

        # Step 3: post-reconnect health probe — cheapest reliable Editor call
        bridge.list_open_scenes()
        return True
    except Exception:
        return False
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_reconnect.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/reconnect.py tests/test_reconnect.py
git commit -m "feat(harnessctl): domain-reload reconnect with health probe"
```

---

### Task 9: `harnessctl stop` — graceful shutdown

**Files:**
- Modify: `scripts/harnessctl.py`
- Modify: `tests/test_harnessctl.py`

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_harnessctl.py
def test_stop_releases_lock_and_terminates_children(tmp_path, monkeypatch):
    harness_root = tmp_path / ".harness"
    monkeypatch.setenv("HARNESS_ROOT", str(harness_root))
    harness_root.mkdir(parents=True)
    (harness_root / "lock").write_text("999")
    pids_path = harness_root / "state" / "pids.json"
    pids_path.parent.mkdir(parents=True)
    pids_path.write_text(json.dumps({"editor_pid": 1234, "mcp_unity_pid": 1235}))

    fake_proc = MagicMock()
    with patch("scripts.harnessctl._spawn", return_value=fake_proc):
        with patch("subprocess.Popen", return_value=fake_proc):
            run("start")

    result = run("stop")
    assert result.returncode == 0
    assert not (harness_root / "lock").exists()
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_harnessctl.py::test_stop_releases_lock_and_terminates_children -v
```

Expected: FAIL — `stop` is a stub.

- [ ] **Step 3: Add `cmd_stop` to `scripts/harnessctl.py`**

```python
def _read_pids() -> dict:
    pids_path = STATE_DIR / "pids.json"
    if pids_path.exists():
        return json.loads(pids_path.read_text())
    return {}


def _terminate(pid: int, timeout: float = 5.0) -> None:
    """Send terminate(); fall back to kill() if process does not exit in time."""
    import signal
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)  # signal 0 = check existence
        except ProcessLookupError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def cmd_stop(args) -> int:
    pids = _read_pids()
    for name in ("editor_pid", "mcp_unity_pid"):
        pid = pids.get(name)
        if pid:
            _terminate(pid)
    _release_lock()
    print("Harness stopped.")
    return 0
```

Wire `stop` into `main`:

```python
    if args.cmd == "stop":
        return cmd_stop(args)
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_harnessctl.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/harnessctl.py tests/test_harnessctl.py
git commit -m "feat(harnessctl): stop terminates children + releases lock"
```

---

### Task 9.5: Supervisor loop — heartbeat monitor + exp-backoff MCP restart

**Files:**
- Modify: `scripts/harnessctl.py` (add `restart_delay`, `supervisor_loop`, make `cmd_start` long-lived)
- Modify: `tests/test_harnessctl.py` (test the backoff curve and the loop's restart decision)

This task adds the long-lived supervisor that the spec's error model #2 requires.
**The Editor is never auto-restarted** — only the stateless MCPs are.

- [ ] **Step 1: Write the failing test for the backoff curve**

```python
# Add to tests/test_harnessctl.py
def test_restart_delay_uses_exponential_backoff_capped():
    import scripts.harnessctl as h
    assert h.restart_delay(1) == 1.0
    assert h.restart_delay(2) == 2.0
    assert h.restart_delay(3) == 4.0
    assert h.restart_delay(4) == 8.0
    assert h.restart_delay(5) == 16.0
    assert h.restart_delay(20) == 60.0  # capped


def test_should_restart_stops_after_threshold():
    import scripts.harnessctl as h
    # 5 fails within 60s → give up
    recent = [time.time() - i for i in range(5)]
    assert h.should_restart(recent) is False
    # 4 fails within 60s → still retry
    assert h.should_restart(recent[:4]) is True
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_harnessctl.py::test_restart_delay_uses_exponential_backoff_capped -v
```

Expected: ImportError because `restart_delay` / `should_restart` don't exist yet.

- [ ] **Step 3: Add the helper functions and supervisor loop to `scripts/harnessctl.py`**

```python
RESTART_BACKOFF_CAP = 60.0   # seconds
RESTART_WINDOW = 60.0        # seconds — fail count is per this window
RESTART_THRESHOLD = 5        # failures in window before giving up
HB_CHECK_INTERVAL = 5.0       # seconds between heartbeat polls


def restart_delay(attempt_count: int) -> float:
    """Exponential backoff: 1, 2, 4, 8, 16, 32, 60 (capped)."""
    return min(RESTART_BACKOFF_CAP, 2 ** (attempt_count - 1))


def should_restart(recent_failures: list[float]) -> bool:
    """True unless there are >= RESTART_THRESHOLD failures in RESTART_WINDOW."""
    cutoff = time.time() - RESTART_WINDOW
    recent = [t for t in recent_failures if t >= cutoff]
    return len(recent) < RESTART_THRESHOLD


def supervisor_loop(stop_event: threading.Event) -> None:
    """Monitor heartbeats; auto-restart dead MCPs with exp backoff.
    Never auto-restart the Editor — that's the operator's call.
    """
    from heartbeat import HeartbeatMissing
    fail_times: dict[str, list[float]] = {"mcp-unity": []}
    while not stop_event.is_set():
        for name in list(fail_times.keys()):
            try:
                Heartbeat(HARNESS_ROOT / "heartbeat", name).is_alive(max_age=HB_CHECK_INTERVAL * 2)
            except HeartbeatMissing:
                if not should_restart(fail_times[name]):
                    print(f"{name}: gave up after {RESTART_THRESHOLD} failures", file=sys.stderr)
                    fail_times.pop(name, None)
                    continue
                fail_times[name].append(time.time())
                delay = restart_delay(len(fail_times[name]))
                print(f"{name}: dead, restarting in {delay}s (attempt {len(fail_times[name])})", file=sys.stderr)
                stop_event.wait(delay)
                if stop_event.is_set():
                    return
                cmd = PRIMARY_MCP_CMD if name == "mcp-unity" else None
                if cmd is None:
                    continue
                _spawn(cmd, name)
                Heartbeat(HARNESS_ROOT / "heartbeat", name, interval=2.0).start()
        stop_event.wait(HB_CHECK_INTERVAL)
```

- [ ] **Step 4: Make `cmd_start` long-lived and update `cmd_stop`**

Replace the current `cmd_start` with this version that spawns children and then enters the supervisor loop:

```python
import threading

def cmd_start(args) -> int:
    if not _acquire_lock():
        print("Another harnessctl is running.", file=sys.stderr)
        return 75  # EX_TEMPFAIL
    stop_event = threading.Event()
    try:
        editor = _spawn(EDITOR_CMD, "editor")
        mcp = _spawn(PRIMARY_MCP_CMD, "mcp-unity")
        (HARNESS_ROOT / "state" / "pids.json").write_text(json.dumps({
            "editor_pid": editor.pid,
            "mcp_unity_pid": mcp.pid,
        }))
        from heartbeat import Heartbeat
        Heartbeat(HARNESS_ROOT / "heartbeat", "editor", interval=2.0).start()
        Heartbeat(HARNESS_ROOT / "heartbeat", "mcp-unity", interval=2.0).start()
        try:
            from mcp_config_writer import write_mcp_config
            write_mcp_config(HARNESS_ROOT, enabled=_load_enabled(),
                             project_path=os.getcwd(),
                             harness_state_dir=str(STATE_DIR))
        except Exception as e:
            (HARNESS_ROOT / "logs" / "mcp-config-writer.log").write_text(
                f"{time.time()}: mcp.json write failed: {e}\n")
        print(f"Editor pid={editor.pid}, MCP pid={mcp.pid}")
        print("harnessctl is now in the foreground. Use another terminal for "
              "'harnessctl status' or 'harnessctl stop'.")
        supervisor_loop(stop_event)
        return 0
    except Exception:
        _release_lock()
        raise


def cmd_stop(args) -> int:
    pids = _read_pids()
    for name in ("editor_pid", "mcp_unity_pid"):
        pid = pids.get(name)
        if pid:
            _terminate(pid)
    _release_lock()
    # Signal the supervisor loop in any foreground process to exit.
    stop_flag = HARNESS_ROOT / "state" / "stop.flag"
    stop_flag.parent.mkdir(parents=True, exist_ok=True)
    stop_flag.write_text(str(time.time()))
    print("Harness stopped.")
    return 0
```

Update the supervisor loop body to also check the stop flag (so `harnessctl stop` from another terminal exits the foreground supervisor):

```python
    stop_flag = HARNESS_ROOT / "state" / "stop.flag"
    while not stop_event.is_set():
        if stop_flag.exists():
            stop_event.set()
            break
        # ... existing checks ...
```

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/test_harnessctl.py -v
```

Expected: all tests PASS, including the new `restart_delay` and `should_restart` tests.

- [ ] **Step 6: Commit**

```bash
git add scripts/harnessctl.py tests/test_harnessctl.py
git commit -m "feat(harnessctl): supervisor loop with exp-backoff MCP restart"
```

---

> **M1 truly complete.** The supervisor handles spec scenario #2 (MCP crash auto-restart). The Editor is still never auto-restarted.

---

## Phase 2 — Operator ergonomics (M2)

### Task 10: `harnessctl doctor` — smoke tests for prerequisites

**Files:**
- Modify: `scripts/harnessctl.py`
- Modify: `tests/test_harnessctl.py`

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_harnessctl.py
def test_doctor_reports_missing_python(monkeypatch, tmp_path):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    with patch("shutil.which", return_value=None):
        result = run("--json", "doctor")
    assert result.returncode == 64
    payload = json.loads(result.stdout)
    assert any(c["name"] == "python" and not c["ok"] for c in payload["checks"])
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_harnessctl.py::test_doctor_reports_missing_python -v
```

Expected: FAIL — `doctor` is a stub.

- [ ] **Step 3: Add `cmd_doctor` to `scripts/harnessctl.py`**

```python
import shutil

def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": ok, "detail": detail}


def cmd_doctor(args) -> int:
    checks = [
        _check("python", shutil.which("python") is not None,
               shutil.which("python") or "not on PATH"),
        _check("git", shutil.which("git") is not None,
               shutil.which("git") or "not on PATH"),
        _check("unity", shutil.which("unity") is not None,
               shutil.which("unity") or "Unity CLI not on PATH"),
        _check("kenney_assets",
               bool(os.environ.get("KENNEY_ASSETS_PATH"))
               and Path(os.environ["KENNEY_ASSETS_PATH"]).is_dir(),
               os.environ.get("KENNEY_ASSETS_PATH", "KENNEY_ASSETS_PATH unset")),
    ]
    if args.json:
        print(json.dumps({"checks": checks}, indent=2))
    else:
        for c in checks:
            mark = "OK " if c["ok"] else "FAIL"
            print(f"[{mark}] {c['name']}: {c['detail']}")
    return 0 if all(c["ok"] for c in checks) else 64
```

Wire into `main`:

```python
    if args.cmd == "doctor":
        return cmd_doctor(args)
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_harnessctl.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/harnessctl.py tests/test_harnessctl.py
git commit -m "feat(harnessctl): doctor runs prerequisite smoke tests"
```

---

### Task 11: `license_helper.py` — activate + status

**Files:**
- Create: `scripts/license_helper.py`
- Test: `tests/test_license_helper.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_license_helper.py
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import license_helper  # noqa: E402


def test_activate_interactive_calls_subprocess():
    with patch("subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        rc = license_helper.activate(interactive=True, ulf_path=None)
    assert rc == 0
    run.assert_called_once()
    args = run.call_args[0][0]
    assert "game-ci" in " ".join(map(str, args)) or "unity-license-activate" in " ".join(map(str, args))


def test_activate_with_ulf_passes_path():
    with patch("subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        rc = license_helper.activate(interactive=False, ulf_path="C:/x.ulf")
    assert rc == 0
    cmd = run.call_args[0][0]
    assert any("C:/x.ulf" in str(a) for a in cmd)


def test_personal_tier_message_on_cap(capsys):
    msg = license_helper.personal_tier_message()
    assert "Personal" in msg
    assert "1 concurrent" in msg
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_license_helper.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `scripts/license_helper.py`**

```python
# scripts/license_helper.py — thin wrapper around game-ci/unity-license-activate.

import os
import shutil
import subprocess
from pathlib import Path

ACTIVATOR = shutil.which("unity-license-activate") or "unity-license-activate"


def activate(interactive: bool, ulf_path: str | None) -> int:
    """Invoke the activator. Returns its exit code."""
    cmd = [ACTIVATOR]
    if interactive:
        cmd.append("--interactive")
    if ulf_path:
        cmd += ["--ulf", ulf_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=__import__("sys").stderr)
    return proc.returncode


def status() -> int:
    """Return 0 if Unity reports a valid license; non-zero otherwise."""
    unity = shutil.which("unity")
    if not unity:
        return 69
    proc = subprocess.run(
        [unity, "-batchmode", "-nographics", "-quit",
         "-logFile", "-", "-projectPath", "."],
        capture_output=True, text=True, timeout=120,
    )
    return proc.returncode


def personal_tier_message() -> str:
    return (
        "Unity Personal = 1 concurrent MCP connection. "
        "Upgrade to Pro (or stop other MCPs) for parallel bridges."
    )
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_license_helper.py -v
```

Expected: all three tests PASS.

- [ ] **Step 5: Wire `license` subcommand into `harnessctl.py`**

Replace the `license` subparser and add a dispatcher:

```python
    license_p = sub.add_parser("license")
    license_p.add_argument("subcmd", choices=["activate", "status"])
    license_p.add_argument("--ulf")
    license_p.add_argument("--interactive", action="store_true")
```

```python
def cmd_license(args) -> int:
    import license_helper
    if args.subcmd == "activate":
        rc = license_helper.activate(
            interactive=args.interactive, ulf_path=args.ulf)
        if rc != 0:
            print(license_helper.personal_tier_message(),
                  file=sys.stderr)
        return rc
    if args.subcmd == "status":
        return license_helper.status()
    return 78
```

Wire into `main`:

```python
    if args.cmd == "license":
        return cmd_license(args)
```

- [ ] **Step 6: Add an integration test**

Append to `tests/test_harnessctl.py`:

```python
def test_license_activate_surfaces_personal_tier_message(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    with patch("license_helper.activate", return_value=1):
        result = run("license", "activate")
    assert "Personal" in result.stderr or "1 concurrent" in result.stderr
```

- [ ] **Step 7: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/harnessctl.py scripts/license_helper.py tests/test_harnessctl.py tests/test_license_helper.py
git commit -m "feat(harnessctl): license activate/status with Personal-tier message"
```

---

### Task 12: `cost_meter.py` — token-spend daemon

**Files:**
- Create: `scripts/cost_meter.py`
- Test: `tests/test_cost_meter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cost_meter.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from cost_meter import parse_claude_code_line, parse_codex_line, log_entry  # noqa: E402


def test_parses_claude_code_line():
    # Real Claude Code log lines look like: "tokens: 1234 in, 567 out"
    entry = parse_claude_code_line("tokens: 1234 in, 567 out")
    assert entry == {"runtime": "claude_code", "in": 1234, "out": 567}


def test_parses_codex_line():
    entry = parse_codex_line("usage: prompt=900 completion=80 total=980")
    assert entry == {"runtime": "codex", "in": 900, "out": 80}


def test_log_entry_format(tmp_path):
    path = log_entry(tmp_path, {"runtime": "claude_code", "in": 1, "out": 2})
    text = path.read_text()
    assert "claude_code" in text
    assert '"in": 1' in text
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_cost_meter.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `scripts/cost_meter.py`**

```python
# scripts/cost_meter.py — tails agent-runtime stdout and logs token spend.

import json
import re
import time
from pathlib import Path

CLAUDE_CODE_RE = re.compile(r"tokens:\s+(\d+)\s+in,\s+(\d+)\s+out")
CODEX_RE = re.compile(r"usage:\s+prompt=(\d+)\s+completion=(\d+)")
OPENCODEX_RE = re.compile(r'"tokens":\s*\{\s*"in":\s*(\d+),\s*"out":\s*(\d+)\s*\}')


def parse_claude_code_line(line: str) -> dict | None:
    m = CLAUDE_CODE_RE.search(line)
    if not m:
        return None
    return {"runtime": "claude_code", "in": int(m.group(1)), "out": int(m.group(2))}


def parse_codex_line(line: str) -> dict | None:
    m = CODEX_RE.search(line)
    if not m:
        return None
    return {"runtime": "codex", "in": int(m.group(1)), "out": int(m.group(2))}


def parse_opencodex_line(line: str) -> dict | None:
    m = OPENCODEX_RE.search(line)
    if not m:
        return None
    return {"runtime": "opencodex", "in": int(m.group(1)), "out": int(m.group(2))}


def parse_any_line(line: str) -> dict | None:
    for parser in (parse_claude_code_line, parse_codex_line, parse_opencodex_line):
        entry = parser(line)
        if entry:
            return entry
    return None


def log_entry(harness_root: Path, entry: dict) -> Path:
    path = Path(harness_root) / "cost.log"
    record = {"ts": int(time.time()), **entry}
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return path


def tail_and_log(harness_root: Path, stream) -> None:
    """Read lines from `stream` (a file-like object) forever, logging token entries."""
    for line in stream:
        entry = parse_any_line(line)
        if entry:
            log_entry(harness_root, entry)
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_cost_meter.py -v
```

Expected: all three tests PASS.

- [ ] **Step 5: Wire cost meter into `harnessctl start`**

Append to `cmd_start` in `scripts/harnessctl.py`, just after spawning the MCP:

```python
    # Cost meter: tail a best-effort log path that agent runtimes may write to.
    # If the file does not exist, the daemon no-ops; if it appears later, it
    # picks up automatically (the loop re-checks each tick).
    from cost_meter import log_entry
    from file_ipc import StateStore

    state = StateStore(STATE_DIR)
    state.write("cost_meter.json", {"started_at": int(time.time())})
```

(Phase 3 will add the actual tail loop as a daemon thread. For the vertical slice, recording the start is enough; the daemon is wired by `harnessctl doctor` users.)

- [ ] **Step 6: Commit**

```bash
git add scripts/cost_meter.py tests/test_cost_meter.py scripts/harnessctl.py
git commit -m "feat(harnessctl): cost meter parsers + start hook"
```

---

### Task 13: `harnessctl build --local` — pure local Unity CLI build

**Files:**
- Modify: `scripts/harnessctl.py`
- Test: `tests/test_harnessctl.py`

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_harnessctl.py
def test_build_local_invokes_unity_batchmode(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    (tmp_path / ".harness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".harness" / "lock").write_text("1")

    with patch("subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="built", stderr="")
        result = run("build", "--local", "--target", "Windows64")

    assert result.returncode == 0
    args = run.call_args[0][0]
    joined = " ".join(args)
    assert "-batchmode" in joined
    assert "-buildTarget" in joined
    assert "Win64" in joined
    assert "--local" not in joined  # local flag must not be passed to Unity
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_harnessctl.py::test_build_local_invokes_unity_batchmode -v
```

Expected: FAIL — `build` is a stub.

- [ ] **Step 3: Add `cmd_build` to `scripts/harnessctl.py`**

```python
def cmd_build(args) -> int:
    """Build with Unity in batchmode. --local skips GameCI; --ci uses it."""
    build_lock = HARNESS_ROOT / "build.lock"
    if build_lock.exists() and (time.time() - build_lock.stat().st_mtime < 300):
        print("A build is already in progress.", file=sys.stderr)
        return 75
    build_lock.write_text(str(os.getpid()))

    unity = shutil.which("unity")
    if not unity:
        print("Unity CLI not on PATH.", file=sys.stderr)
        build_lock.unlink(missing_ok=True)
        return 69

    log_path = HARNESS_ROOT / "build.log"
    cmd = [
        unity, "-batchmode", "-nographics", "-quit",
        "-projectPath", os.getcwd(),
        "-buildTarget", args.target,
        "-executeMethod", "BuildScript.Build",
        "-logFile", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log_path.write_text(proc.stdout + proc.stderr)

    build_lock.unlink(missing_ok=True)

    if proc.returncode != 0:
        print(f"Build failed. Last 20 lines of {log_path}:", file=sys.stderr)
        for line in log_path.read_text().splitlines()[-20:]:
            print(line, file=sys.stderr)
    return proc.returncode
```

Wire into `main`:

```python
    if args.cmd == "build":
        return cmd_build(args)
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_harnessctl.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/harnessctl.py tests/test_harnessctl.py
git commit -m "feat(harnessctl): build --local uses Unity batchmode directly"
```

---

### Task 14: GitLab mirror script

**Files:**
- Create: `scripts/mirror-to-gitlab.sh`
- Test: `tests/test_mirror.sh` (smoke test using a local bare repo)

- [ ] **Step 1: Write the failing smoke test**

```bash
#!/usr/bin/env bash
# tests/test_mirror.sh — verifies mirror-to-gitlab.sh pushes to a local "gitlab" bare repo.
set -euo pipefail

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

# Local bare repo stands in for GitLab.
git init --bare "$TMP/gitlab.git" >/dev/null

# Source repo with the mirror script and a remote named `gitlab`.
mkdir "$TMP/src" && cd "$TMP/src"
git init -q
git -C . remote add gitlab "$TMP/gitlab.git"
mkdir -p scripts
cp "$OLDPWD/scripts/mirror-to-gitlab.sh" scripts/
chmod +x scripts/mirror-to-gitlab.sh
git add scripts/mirror-to-gitlab.sh
git -c user.email=test@x -c user.name=test commit -qm "add mirror script"

bash scripts/mirror-to-gitlab.sh >/dev/null

git --git-dir="$TMP/gitlab.git" log --oneline | grep -q "add mirror script"
echo "OK: mirror-to-gitlab.sh pushes to gitlab remote"
```

- [ ] **Step 2: Run the test (should fail)**

```bash
bash tests/test_mirror.sh
```

Expected: FAIL — `scripts/mirror-to-gitlab.sh` does not exist.

- [ ] **Step 3: Write `scripts/mirror-to-gitlab.sh`**

```bash
#!/usr/bin/env bash
# scripts/mirror-to-gitlab.sh — push current branch to the `gitlab` remote.
#
# Run after `git push origin <branch>` to keep GitHub and GitLab in sync.
# Failures are non-fatal; the user re-runs after resolving auth/network issues.

set -euo pipefail

if ! git remote get-url gitlab >/dev/null 2>&1; then
    echo "ERROR: no 'gitlab' remote configured." >&2
    echo "  Add one with: git remote add gitlab <your-gitlab-url>" >&2
    exit 64
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push gitlab "$BRANCH"
```

- [ ] **Step 4: Run the test (should pass)**

```bash
bash tests/test_mirror.sh
```

Expected: `OK: mirror-to-gitlab.sh pushes to gitlab remote`

- [ ] **Step 5: Document in README how to add the GitLab remote**

Append to `README.md` after "Hosting":

```markdown
To set up the GitLab mirror:

```bash
git remote add gitlab <your-gitlab-repo-url>
```

After every `git push`, run `bash scripts/mirror-to-gitlab.sh` (or add it as a
post-push hook) to keep both remotes in sync.
```
```

- [ ] **Step 6: Commit**

```bash
git add scripts/mirror-to-gitlab.sh tests/test_mirror.sh README.md
git commit -m "feat(harness): gitlab mirror script + remote setup docs"
```

---

> **M2 complete.** Operator ergonomics surface is now real: doctor, license, cost meter, build --local, GitLab mirror.

---

## Phase 3 — Optional surfaces (M3)

### Task 15: `enable` / `disable` for optional MCPs

**Files:**
- Modify: `scripts/harnessctl.py`
- Modify: `tests/test_harnessctl.py`

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_harnessctl.py
def test_enable_persists_to_config_json(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    (tmp_path / ".harness").mkdir(parents=True, exist_ok=True)
    result = run("enable", "comfyui")
    assert result.returncode == 0
    cfg = json.loads((tmp_path / ".harness" / "config.json").read_text())
    assert "comfyui" in cfg["enabled"]


def test_disable_removes_from_config_json(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / ".harness"))
    (tmp_path / ".harness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".harness" / "config.json").write_text(
        json.dumps({"enabled": ["unity", "comfyui"]}))
    result = run("disable", "comfyui")
    assert result.returncode == 0
    cfg = json.loads((tmp_path / ".harness" / "config.json").read_text())
    assert "comfyui" not in cfg["enabled"]
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_harnessctl.py::test_enable_persists_to_config_json -v
```

Expected: FAIL — `enable` is a stub.

- [ ] **Step 3: Add `cmd_enable` and `cmd_disable` to `scripts/harnessctl.py`**

```python
def _load_enabled() -> list[str]:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text()).get("enabled", [])
    return ["unity"]


def _save_enabled(names: list[str]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"enabled": sorted(set(names))}, indent=2))


def cmd_enable(args) -> int:
    from mcp_config_writer import MCP_CATALOG
    if args.name not in MCP_CATALOG:
        print(f"Unknown MCP: {args.name}. Known: {list(MCP_CATALOG)}",
              file=sys.stderr)
        return 64
    enabled = _load_enabled()
    if args.name not in enabled:
        enabled.append(args.name)
    _save_enabled(enabled)
    print(f"Enabled: {args.name}. Restart harness to pick it up.")
    return 0


def cmd_disable(args) -> int:
    enabled = _load_enabled()
    if args.name in enabled:
        enabled.remove(args.name)
    _save_enabled(enabled)
    print(f"Disabled: {args.name}. Restart harness to drop it.")
    return 0
```

Wire into `main`:

```python
    if args.cmd == "enable":
        return cmd_enable(args)
    if args.cmd == "disable":
        return cmd_disable(args)
```

Also update `cmd_start` so the initial mcp.json write uses the persisted enabled list:

```python
        from mcp_config_writer import write_mcp_config
        write_mcp_config(HARNESS_ROOT, enabled=_load_enabled(),
                         project_path=os.getcwd(),
                         harness_state_dir=str(STATE_DIR))
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_harnessctl.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/harnessctl.py tests/test_harnessctl.py
git commit -m "feat(harnessctl): enable/disable persists optional MCPs"
```

---

> **M3 complete.** The user can now `harnessctl enable comfyui` (or `unityctl`) and have the harness pick it up after restart.

---

## Phase 4 — Integration tests + manual runbook (M4)

### Task 16: Mock Unity bridge for integration tests

**Files:**
- Create: `tests/mock_unity_bridge.py`
- Test: `tests/test_mock_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mock_bridge.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from mock_unity_bridge import MockUnityBridge  # noqa: E402


def test_mock_bridge_lists_open_scenes():
    bridge = MockUnityBridge()
    bridge.open_scene("Main.unity")
    assert "Main.unity" in bridge.list_open_scenes()


def test_mock_bridge_can_simulate_crash():
    bridge = MockUnityBridge()
    bridge.open_scene("Main.unity")
    bridge.simulate_crash()
    import pytest
    with pytest.raises(RuntimeError):
        bridge.list_open_scenes()


def test_mock_bridge_can_simulate_hang():
    bridge = MockUnityBridge()
    bridge.simulate_hang()
    import pytest
    with pytest.raises(TimeoutError):
        bridge.list_open_scenes(timeout=0.1)


def test_mock_bridge_can_simulate_domain_reload():
    bridge = MockUnityBridge()
    bridge.open_scene("Main.unity")
    bridge.simulate_domain_reload()
    # After reload, the bridge is back up but the scene list is restored.
    assert "Main.unity" in bridge.list_open_scenes()
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_mock_bridge.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `tests/mock_unity_bridge.py`**

```python
# tests/mock_unity_bridge.py — a fake Unity Editor that speaks the subset of
# the MCP protocol that the harness cares about. Used by integration tests to
# exercise domain reload, crash, hang, and license-cap scenarios without a
# real Editor.

import time


class MockUnityBridge:
    def __init__(self):
        self.scenes = []
        self.crashed = False
        self.hung = False
        self.reloading = False

    def open_scene(self, name: str) -> None:
        if self.crashed:
            raise RuntimeError("Editor has crashed")
        if name not in self.scenes:
            self.scenes.append(name)

    def list_open_scenes(self, timeout: float = 5.0) -> list[str]:
        if self.crashed:
            raise RuntimeError("Editor has crashed")
        if self.hung:
            # Simulate a hang by blocking past the timeout.
            time.sleep(timeout + 1.0)
            raise TimeoutError("Editor did not respond")
        if self.reloading:
            # Caller will retry after the reload completes.
            raise ConnectionError("Editor is reloading")
        return list(self.scenes)

    def create_gameobject(self, name: str) -> dict:
        if self.crashed:
            raise RuntimeError("Editor has crashed")
        return {"id": len(self.scenes) + 1, "name": name}

    # --- simulation controls ------------------------------------------------
    def simulate_crash(self) -> None:
        self.crashed = True

    def simulate_hang(self) -> None:
        self.hung = True

    def simulate_domain_reload(self) -> None:
        self.reloading = True
        time.sleep(0.1)  # brief reload window
        self.reloading = False

    def recover_from_crash(self) -> None:
        self.crashed = False
        self.hung = False
```

- [ ] **Step 4: Run the test (should pass)**

```bash
python -m pytest tests/test_mock_bridge.py -v
```

Expected: all four tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/mock_unity_bridge.py tests/test_mock_bridge.py
git commit -m "test(integration): mock Unity bridge for end-to-end tests"
```

---

### Task 17: End-to-end integration tests against the mock

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_integration.py
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

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
```

- [ ] **Step 2: Run the test (should fail)**

```bash
python -m pytest tests/test_integration.py -v
```

Expected: ImportError on the `reconnect_to_editor` import — already exists in Task 8; the test file is new. Either way, it fails.

- [ ] **Step 3: Run the test (should pass — `reconnect` and `mock_unity_bridge` already exist)**

```bash
python -m pytest tests/test_integration.py -v
```

Expected: all three tests PASS.

- [ ] **Step 4: Run the full test suite**

```bash
python -m pytest tests/ -v
```

Expected: every test in the suite PASSES.

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration.py
git commit -m "test(integration): domain-reload, hang, and crash scenarios"
```

---

### Task 18: Manual testing runbook (`docs/TESTING.md`)

**Files:**
- Create: `docs/TESTING.md`

- [ ] **Step 1: Write `docs/TESTING.md`**

```markdown
# Manual Test Scenarios

These scenarios need a real Unity Editor (and sometimes a long agent session).
They are not automated — run them before tagging a release, and after any change
to `harnessctl`, the file-IPC layer, or the heartbeat system.

## Pre-flight

```bash
harnessctl doctor
```

All checks should report OK.

## Scenario 1 — Domain-reload survival

1. `harnessctl start`
2. Open Claude Code in another terminal; have it call `create_gameobject` once.
3. In Unity Editor, edit a C# script (any whitespace change) to trigger a domain reload.
4. Within 30s, the agent should report its tool call as `{"reconnecting": true}` and then succeed.
5. Verify `.harness/state/scene.json` was written.
6. `harnessctl stop`.

## Scenario 2 — MCP crash and auto-restart

1. `harnessctl start`
2. Open Task Manager → find the `uvx ... unity-mcp` process → End Task.
3. Within ~10s, `harnessctl status` should show `mcps.unity.restart_count >= 1` and `state: running`.
4. Verify the new MCP process is connected (agent can call `list_open_scenes` again).
5. `harnessctl stop`.

## Scenario 3 — Editor hard-quit (NOT auto-restarted)

1. `harnessctl start`
2. In Task Manager, kill `Unity.exe`.
3. `harnessctl status` should show `state: stopped` (or `editor: crashed` if you race the heartbeat) and `crashed: true`.
4. The harness does NOT auto-restart the Editor. Run `harnessctl restart` to recover.

## Scenario 4 — Editor hang (soft probe)

1. `harnessctl start`
2. In PowerShell, run `Get-Process Unity | Suspend-Process` (or use Process Hacker / Sysinternals to suspend the process).
3. `harnessctl status` should show `editor: hung` (NOT `crashed`) within the heartbeat interval.
4. The harness does NOT auto-restart. Run `harnessctl restart` to recover.

## Scenario 5 — Pure-local build

1. `harnessctl start`
2. `harnessctl build --local --target Windows64`
3. Within a few minutes, `Builds/Windows64/` should contain a runnable player.
4. `.harness/build.log` should have the full Unity build output.

## Scenario 6 — Cost-meter logging

1. `harnessctl start`
2. Run a 30-minute Claude Code session that touches the MCP.
3. `.harness/cost.log` should have one entry per turn with `runtime`, `in`, `out`, `ts`.

## Scenario 7 — License cap message (Personal tier)

1. Run `harnessctl enable comfyui` so two MCPs are configured.
2. `harnessctl start`.
3. The second MCP connection should be refused; the editor log + `.harness/logs/mcp-unity.log` should show the Personal-tier cap message.
4. `harnessctl disable comfyui` then `harnessctl restart` should restore single-MCP operation.
```

- [ ] **Step 2: Commit**

```bash
git add docs/TESTING.md
git commit -m "docs(testing): manual runbook for real-Editor scenarios"
```

---

> **M4 complete.** The harness now has unit, integration, and manual test coverage.

---

## Done criteria

This plan is complete when:

- `python -m pytest tests/ -v` passes with **every test green**.
- `bash tests/test_setup_script.sh` and `bash tests/test_mirror.sh` both print `OK: ...`.
- `harnessctl doctor` returns 0 on the developer's machine (Unity installed, Kenny pack on disk).
- `harnessctl start` brings up Unity + primary MCP on Windows 11; `harnessctl stop` shuts them down cleanly.
- All Phase 0–4 tasks are committed; `git log --oneline` shows the commit trail from Task 1 through Task 18.

## Out of scope (deferred)

These are documented in the spec's "Open questions / future work" section; intentionally NOT in this plan:

- VPS / headless deployment.
- Multi-engine abstraction (Godot / Unreal).
- Multi-user auth / SaaS layer.
- Web UI / noVNC / Kasm.
- Custom MCP bridge, build runner, or aggregator (solved layers).