#!/usr/bin/env python3
"""Per-process heartbeat files used to detect crashes/hangs."""

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
