#!/usr/bin/env python3
"""Unity AI Harness supervisor."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

HARNESS_ROOT = Path(os.environ.get("HARNESS_ROOT", Path.cwd() / ".harness"))
LOCK_FILE = HARNESS_ROOT / "lock"
STATE_DIR = HARNESS_ROOT / "state"
CONFIG_FILE = HARNESS_ROOT / "config.json"


def _now() -> float:
    return time.time()


def status_payload() -> dict:
    """Return the canonical harness state. Read-only."""
    running = LOCK_FILE.exists() and (LOCK_FILE.stat().st_mtime > (_now() - 300))
    return {
        "state": "running" if running else "stopped",
        "harness_root": str(HARNESS_ROOT),
        "editor": None,
        "mcps": {},
    }


def cmd_status(args) -> int:
    payload = status_payload()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Harness: {payload['state']}")
        print(f"Root:    {payload['harness_root']}")
    return 0


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

    sub.add_parser("doctor").add_argument("--json", action="store_true", help="machine-readable output")
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
    print(f"(stub) {args.cmd} not implemented yet", file=sys.stderr)
    return 78  # EX_CONFIG


if __name__ == "__main__":
    sys.exit(main())
