#!/usr/bin/env python3
"""Unity AI Harness supervisor."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HARNESS_ROOT = Path(os.environ.get("HARNESS_ROOT", Path.cwd() / ".harness"))
LOCK_FILE = HARNESS_ROOT / "lock"
STATE_DIR = HARNESS_ROOT / "state"
CONFIG_FILE = HARNESS_ROOT / "config.json"

EDITOR_CMD = ["unity", "-projectPath", "."]
PRIMARY_MCP_CMD = [
    "uvx",
    "--from",
    "git+https://github.com/CoplayDev/unity-mcp.git",
    "unity-mcp",
]


def _now() -> float:
    return time.time()


def status_payload() -> dict:
    """Return the canonical harness state. Read-only."""
    running = LOCK_FILE.exists() and (LOCK_FILE.stat().st_mtime > (_now() - 300))
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


def cmd_status(args) -> int:
    payload = status_payload()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Harness: {payload['state']}")
        print(f"Root:    {payload['harness_root']}")
    return 0


def _acquire_lock() -> bool:
    """Return True if we acquired the lock; False if another harnessctl holds it."""
    HARNESS_ROOT.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists() and (LOCK_FILE.stat().st_mtime > (_now() - 300)):
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
        cmd,
        stdout=log,
        stderr=subprocess.STDOUT,
        cwd=os.getcwd(),
    )


def cmd_start(args) -> int:
    if not _acquire_lock():
        print("Another harnessctl is running.", file=sys.stderr)
        return 75  # EX_TEMPFAIL
    try:
        editor = _spawn(EDITOR_CMD, "editor")
        mcp = _spawn(PRIMARY_MCP_CMD, "mcp-unity")
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / "pids.json").write_text(
            json.dumps(
                {
                    "editor_pid": editor.pid,
                    "mcp_unity_pid": mcp.pid,
                }
            )
        )
        # Best-effort: regenerate mcp.json for agent runtimes to discover
        try:
            from mcp_config_writer import write_mcp_config

            write_mcp_config(
                HARNESS_ROOT,
                enabled=["unity"],
                project_path=str(Path.cwd()),
                harness_state_dir=str(STATE_DIR),
            )
        except Exception as e:  # non-fatal; doctor will surface
            (HARNESS_ROOT / "logs" / "mcp-config-writer.log").write_text(
                f"{_now()}: mcp.json write failed: {e}\n"
            )
        if args.json:
            print(
                json.dumps(
                    {
                        "editor_pid": editor.pid,
                        "mcp_unity_pid": mcp.pid,
                    },
                    indent=2,
                )
            )
        else:
            print(f"Editor pid={editor.pid}, MCP pid={mcp.pid}")
        return 0
    except Exception:
        _release_lock()
        raise


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harnessctl")
    sub = p.add_subparsers(dest="cmd", required=True)

    start = sub.add_parser("start")
    start.add_argument("--json", action="store_true", help="machine-readable output")

    stop = sub.add_parser("stop")
    stop.add_argument("--json", action="store_true", help="machine-readable output")

    status = sub.add_parser("status")
    status.add_argument("--json", action="store_true", help="machine-readable output")

    restart = sub.add_parser("restart")
    restart.add_argument("--json", action="store_true", help="machine-readable output")

    build = sub.add_parser("build")
    build.add_argument("--target", default="Windows64", help="build target")
    build.add_argument("--local", action="store_true", help="local batchmode build")

    sub.add_parser("doctor").add_argument(
        "--json", action="store_true", help="machine-readable output"
    )
    sub.add_parser("setup")
    enable = sub.add_parser("enable")
    enable.add_argument("name", help="MCP name to enable")
    disable = sub.add_parser("disable")
    disable.add_argument("name", help="MCP name to disable")
    license_parser = sub.add_parser("license")
    license_parser.add_argument("subcmd", nargs="?", help="status | activate")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "start":
        return cmd_start(args)
    print(f"(stub) {args.cmd} not implemented yet", file=sys.stderr)
    return 78  # EX_CONFIG


if __name__ == "__main__":
    sys.exit(main())
