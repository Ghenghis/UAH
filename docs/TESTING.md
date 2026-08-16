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
