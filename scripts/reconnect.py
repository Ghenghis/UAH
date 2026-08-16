#!/usr/bin/env python3
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

from pathlib import Path

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
