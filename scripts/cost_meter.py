#!/usr/bin/env python3
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
