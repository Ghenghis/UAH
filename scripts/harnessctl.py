#!/usr/bin/env python3
"""Unity AI Harness supervisor."""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from heartbeat import Heartbeat, HeartbeatMissing

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

# Build-target aliases so the harness can accept friendly names.
BUILD_TARGET_ALIASES = {
    "Windows64": "Win64",
    "Windows32": "Win32",
    "Linux64": "Linux64",
    "MacOS": "StandaloneOSX",
    "Android": "Android",
    "iOS": "iOS",
    "WebGL": "WebGL",
}

# Supervisor tuning.
RESTART_BACKOFF_CAP = 60.0
RESTART_WINDOW = 60.0
RESTART_THRESHOLD = 5
HB_CHECK_INTERVAL = 5.0


def _now() -> float:
    return time.time()


def _load_enabled() -> list[str]:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text()).get("enabled", [])
    return ["unity"]


def _save_enabled(names: list[str]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"enabled": sorted(set(names))}, indent=2))


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
        s = payload["state"]
        print(f"Harness: {s}")
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


def _read_pids() -> dict:
    pids_path = STATE_DIR / "pids.json"
    if pids_path.exists():
        return json.loads(pids_path.read_text())
    return {}


def _terminate(pid: int, timeout: float = 5.0) -> None:
    """Send terminate(); fall back to kill() if process does not exit in time."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        return
    deadline = _now() + timeout
    while _now() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        except OSError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        pass


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


def restart_delay(attempt_count: int) -> float:
    """Exponential backoff: 1, 2, 4, 8, 16, 32, 60 (capped)."""
    return min(RESTART_BACKOFF_CAP, 2 ** (attempt_count - 1))


def should_restart(recent_failures: list[float]) -> bool:
    """True unless there are >= RESTART_THRESHOLD failures in RESTART_WINDOW."""
    cutoff = _now() - RESTART_WINDOW
    recent = [t for t in recent_failures if t >= cutoff]
    return len(recent) < RESTART_THRESHOLD


def supervisor_loop(stop_event: threading.Event) -> None:
    """Monitor heartbeats; auto-restart dead MCPs with exp backoff.
    Never auto-restart the Editor — that's the operator's call.
    """
    fail_times: dict[str, list[float]] = {"mcp-unity": []}
    stop_flag = HARNESS_ROOT / "state" / "stop.flag"
    while not stop_event.is_set():
        if stop_flag.exists():
            stop_event.set()
            break
        for name in list(fail_times.keys()):
            try:
                Heartbeat(HARNESS_ROOT / "heartbeat", name).is_alive(
                    max_age=HB_CHECK_INTERVAL * 2
                )
            except HeartbeatMissing:
                if not should_restart(fail_times[name]):
                    print(
                        f"{name}: gave up after {RESTART_THRESHOLD} failures",
                        file=sys.stderr,
                    )
                    fail_times.pop(name, None)
                    continue
                fail_times[name].append(_now())
                delay = restart_delay(len(fail_times[name]))
                print(
                    f"{name}: dead, restarting in {delay}s "
                    f"(attempt {len(fail_times[name])})",
                    file=sys.stderr,
                )
                stop_event.wait(delay)
                if stop_event.is_set():
                    return
                cmd = PRIMARY_MCP_CMD if name == "mcp-unity" else None
                if cmd is None:
                    continue
                _spawn(cmd, name)
                Heartbeat(HARNESS_ROOT / "heartbeat", name, interval=2.0).start()
        stop_event.wait(HB_CHECK_INTERVAL)


def cmd_start(args) -> int:
    if not _acquire_lock():
        print("Another harnessctl is running.", file=sys.stderr)
        return 75  # EX_TEMPFAIL
    stop_event = threading.Event()
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

        Heartbeat(HARNESS_ROOT / "heartbeat", "editor", interval=2.0).start()
        Heartbeat(HARNESS_ROOT / "heartbeat", "mcp-unity", interval=2.0).start()

        # Best-effort: regenerate mcp.json for agent runtimes to discover
        try:
            from mcp_config_writer import write_mcp_config

            write_mcp_config(
                HARNESS_ROOT,
                enabled=_load_enabled(),
                project_path=str(Path.cwd()),
                harness_state_dir=str(STATE_DIR),
            )
        except Exception as e:  # non-fatal; doctor will surface
            (HARNESS_ROOT / "logs" / "mcp-config-writer.log").write_text(
                f"{_now()}: mcp.json write failed: {e}\n"
            )

        # Cost meter: mark that this session started.
        try:
            from cost_meter import log_entry
            from file_ipc import StateStore

            state = StateStore(STATE_DIR)
            state.write("cost_meter.json", {"started_at": int(_now())})
        except Exception:
            pass

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
            print(
                "harnessctl is now in the foreground. Use another terminal for "
                "'harnessctl status' or 'harnessctl stop'."
            )
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
    stop_flag.write_text(str(_now()))
    print("Harness stopped.")
    return 0


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


def cmd_license(args) -> int:
    import license_helper

    if args.subcmd == "activate":
        rc = license_helper.activate(
            interactive=args.interactive, ulf_path=args.ulf
        )
        if rc != 0:
            print(license_helper.personal_tier_message(), file=sys.stderr)
        return rc
    if args.subcmd == "status":
        return license_helper.status()
    return 78


def cmd_build(args) -> int:
    """Build with Unity in batchmode. --local skips GameCI; --ci uses it."""
    build_lock = HARNESS_ROOT / "build.lock"
    if build_lock.exists() and (_now() - build_lock.stat().st_mtime < 300):
        print("A build is already in progress.", file=sys.stderr)
        return 75
    build_lock.write_text(str(os.getpid()))

    unity = shutil.which("unity")
    if not unity:
        print("Unity CLI not on PATH.", file=sys.stderr)
        build_lock.unlink(missing_ok=True)
        return 69

    target = BUILD_TARGET_ALIASES.get(args.target, args.target)
    log_path = HARNESS_ROOT / "build.log"
    cmd = [
        unity,
        "-batchmode",
        "-nographics",
        "-quit",
        "-projectPath",
        os.getcwd(),
        "-buildTarget",
        target,
        "-executeMethod",
        "BuildScript.Build",
        "-logFile",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log_path.write_text(proc.stdout + proc.stderr)

    build_lock.unlink(missing_ok=True)

    if proc.returncode != 0:
        print(f"Build failed. Last 20 lines of {log_path}:", file=sys.stderr)
        for line in log_path.read_text().splitlines()[-20:]:
            print(line, file=sys.stderr)
    return proc.returncode


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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harnessctl")
    p.add_argument("--json", action="store_true", help="machine-readable output")
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

    doctor = sub.add_parser("doctor")
    doctor.add_argument("--json", action="store_true", help="machine-readable output")

    sub.add_parser("setup")

    enable = sub.add_parser("enable")
    enable.add_argument("name", help="MCP name to enable")

    disable = sub.add_parser("disable")
    disable.add_argument("name", help="MCP name to disable")

    license_parser = sub.add_parser("license")
    license_parser.add_argument(
        "subcmd", nargs="?", default=None, choices=["activate", "status"]
    )
    license_parser.add_argument("--ulf", default=None, help="path to .ulf file")
    license_parser.add_argument(
        "--interactive", action="store_true", help="interactive activation"
    )

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "start":
        return cmd_start(args)
    if args.cmd == "stop":
        return cmd_stop(args)
    if args.cmd == "doctor":
        return cmd_doctor(args)
    if args.cmd == "license":
        return cmd_license(args)
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "enable":
        return cmd_enable(args)
    if args.cmd == "disable":
        return cmd_disable(args)
    print(f"(stub) {args.cmd} not implemented yet", file=sys.stderr)
    return 78  # EX_CONFIG


if __name__ == "__main__":
    sys.exit(main())
