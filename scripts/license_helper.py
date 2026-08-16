#!/usr/bin/env python3
# scripts/license_helper.py — thin wrapper around game-ci/unity-license-activate.

import os
import shutil
import subprocess
import sys
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
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def status() -> int:
    """Return 0 if Unity reports a valid license; non-zero otherwise."""
    unity = shutil.which("unity")
    if not unity:
        return 69
    proc = subprocess.run(
        [unity, "-batchmode", "-nographics", "-quit",
         "-logFile", "-", "-projectPath", "."],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode


def personal_tier_message() -> str:
    return (
        "Unity Personal = 1 concurrent MCP connection. "
        "Upgrade to Pro (or stop other MCPs) for parallel bridges."
    )
