#!/usr/bin/env python3
"""Durable sidecar state for surviving Unity domain reloads."""

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
