---
title: Unity AI Harness — Local Windows 11 design
date: 2026-08-15
status: approved (sections 1-4); testing section inline; pending final user review
---

# Unity AI Harness — Local Windows 11 design

## 1. Mission

Ship a downloadable, cloneable kit that turns a Windows 11 machine into a self-hosted Unity AI development pipeline. The user (or an AI agent runtime such as Claude Code, Cursor, Codex, or OpenCodex) starts a single command (`harnessctl start`), then drives Unity scenes, scripts, assets, and builds through MCP servers — with the failure modes already handled.

The kit is **stitch-first**: every layer that has a mature open-source replacement is adopted wholesale. New code is only written where no good alternative exists.

## 2. Constraints (from clarifying questions)

| Question | Answer |
|---|---|
| Operator | Solo (just the user) |
| Host | Local Windows 11 machine (no VPS required) |
| Agent location | Flexible — same box, or laptop pointing at it |
| Projects | One at a time |
| Default asset input | Kenny Game Assets All-in-1 v3.6.0 at `G:\Github\Kenney Game Assets All-in-1 3.6.0` (driven by `KENNEY_ASSETS_PATH` env var, not hard-coded) |
| Engine scope | Unity only (Godot explicitly dropped) |
| Hosting of the kit itself | Both GitHub and GitLab (mirrored) |
| Form factor | Native processes — no Docker, no containers |

## 3. Goals and non-goals

**Goals**
- Minimal hand-holding; an agent can drive the pipeline once `harnessctl start` returns.
- Domain-reload survival is a first-class path (the #1 documented failure mode in Unity MCP setups).
- License activation is honest about Personal-tier caps; no circumvention, no "magic."
- Cost visibility per agent session (no OSS project does this; cheap to add).
- Mirror to GitHub + GitLab via a single script.

**Non-goals (explicitly out)**
- Multi-tenant / SaaS layer (no auth, no billing, no queue, no per-user storage).
- Headless VPS deployment (later, if needed; not blocking).
- Multi-engine abstraction (Godot / Unreal / etc.).
- Building an MCP bridge, build runner, or aggregator from scratch — all have mature MIT/Apache options.
- GPL-3.0 contamination — no Kasm/webtop/selkies-gstreamer unless we re-license cleanly.

## 4. Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  Agent runtime                  (external to the kit)          │
│  - Claude Code / Cursor / Codex / OpenCodex                   │
│  - optionally fronted by OpenCodex proxy for model choice     │
└──────────┬─────────────────────────────────────────────────────┘
           │ stdio JSON-RPC (MCP transport)
           ▼
┌────────────────────────────────────────────────────────────────┐
│  MCP servers                   (children of the agent)         │
│  - Primary:  CoplayDev/unity-mcp  (or CoderGamester/mcp-unity) │
│  - Optional: unityctl, comfyui-mcp (enabled on demand)        │
└──────────┬─────────────────────────────────────────────────────┘
           │ WebSocket / named pipe  (Unity bridge)
           ▼
┌────────────────────────────────────────────────────────────────┐
│  Unity Editor                  (long-lived Windows process)    │
│  - CoplayDev UPM package installed                             │
│  - holds scene state, asset DB, scripts                        │
└──────────┬─────────────────────────────────────────────────────┘
           │ JSON sidecars in .harness/state/  (survives domain reload)
           ▼
┌────────────────────────────────────────────────────────────────┐
│  File-IPC state dir             (.harness/state/)              │
│  - scene.json, last-edit.json, last-tool-result.json           │
└────────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────┐
   │  harnessctl.py  (supervisor — the single CLI entry)     │
   │  - owns Editor + MCPs + cost meter lifecycle             │
   │  - invokes license helper on demand                      │
   │  - writes .harness/mcp.json so the agent can discover    │
   │    the running MCP endpoints after `harnessctl start`    │
   └──────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────┐
   │  GameCI           (adopted, invoked only for builds)     │
   └──────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────┐
   │  Kenney asset pack   (external, symlinked via env var)   │
   └──────────────────────────────────────────────────────────┘
```

**Communication paths**
1. Agent → MCP — stdio JSON-RPC.
2. MCP → Editor — CoplayDev's bridge (WebSocket or named pipe).
3. Editor ↔ agent durable state — file-IPC sidecars in `.harness/state/`.
4. harnessctl → all processes — Python supervisor with heartbeat files + PID checks.
5. harnessctl → GameCI — shell-out for builds only (`harnessctl build` or `harnessctl build --local`).

**Trust boundaries**
- Agent runtime is untrusted to the kit (just an MCP consumer).
- Unity Editor is the only stateful piece.
- `.harness/state/` is the durable boundary — survives MCP restarts, domain reloads, agent swaps.
- `mcp.json` is the discoverable config surface for the agent runtime.

## 5. Components

### What the kit builds

| Component | Purpose | Surface | LoC |
|---|---|---|---|
| `harnessctl` | Supervisor for Editor + MCPs + cost meter | `harnessctl {start\|stop\|status\|restart\|build\|license\|doctor\|setup\|enable\|disable}` | ~300 Python |
| File-IPC layer | Persist agent state across domain reloads | JSON files in `.harness/state/*.json` | ~150 Python |
| License helper | Activate Unity Editor | `harnessctl license activate [--ulf <path>]` | ~100 Python (wraps `game-ci/unity-license-activate`) |
| Cost meter | Track token spend per session | daemon; logs to `.harness/cost.log` | ~80 Python |
| Setup script | One-time install | `bash scripts/setup.sh` | ~100 Bash |
| GitLab mirror | Mirror kit repo | `scripts/mirror-to-gitlab.sh` + post-push hook | ~30 Bash |

### What the kit adopts wholesale

| Component | Why adopted |
|---|---|
| `CoplayDev/unity-mcp` | ~47 tools, MIT, most popular Unity MCP. Backup option: `CoderGamester/mcp-unity`. |
| `game-ci/cli` + `unity-builder` | MIT, active 2026, GitHub + GitLab examples included. |
| `butterlatte-zhang/unity-ai-bridge` | Reference for the file-IPC pattern (Apache-2.0). |
| `OpenCodex` (`@bitkyc08/opencodex`) | Model flexibility. npm package; runs on default port 10100. |

### Component boundaries

- `harnessctl` knows nothing about MCP protocol — only process lifecycle.
- MCP servers know nothing about each other — connect to Editor independently.
- File-IPC is the only piece that crosses Editor ↔ agent.
- GameCI is invoked, not embedded.
- `mcp.json` is the discovery surface — `harnessctl start` (re)writes it; agents read it to find stdio command lines.
- Optional MCPs (`unityctl`, `comfyui-mcp`) are toggled via `harnessctl enable <name>` / `harnessctl disable <name>`, persisted to `.harness/config.json`. Default state: only the primary Unity MCP is enabled.

### `mcp.json` shape (for agent runtimes)

```json
{
  "mcpServers": {
    "unity": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/CoplayDev/unity-mcp.git", "unity-mcp"],
      "env": {
        "UNITY_PROJECT_PATH": "<absolute path to the Unity project>",
        "HARNESS_STATE_DIR": "<absolute path to .harness/state>"
      }
    }
  }
}
```

Path: `.harness/mcp.json` (project-relative). Regenerated on every `harnessctl start` and `harnessctl enable/disable`. Agent runtimes (Claude Desktop, Cursor, Codex, OpenCodex) read this file to know which MCPs are available and how to spawn them.

## 6. Data flow

### Flow 1 — First-time setup

```
user → bash scripts/setup.sh
   ├─ git submodule update --init      → clones unity-mcp, game-ci, unity-ai-bridge
   ├─ validate $KENNEY_ASSETS_PATH     → symlinks Assets/_Imported to the pack
   ├─ write Packages/manifest.json     → adds CoplayDev UPM entry
   ├─ write PROJECT-STATUS.md          → initial handoff doc
   └─ harnessctl license activate      → wraps game-ci/unity-license-activate
```

Every step is idempotent. If Kenny is missing, setup prints the expected env var and prompts; it does not fail silently.

### Flow 2 — Agent edits a scene

```
agent ──(create_gameobject)──► CoplayDev MCP ──(ws: create GO)──► Unity Editor
                                                                  │
                                                                  ├─ adds to scene
                                                                  └─ fires scene event ─► write .harness/state/scene.json
agent ◄── tool result {id: 42} ◄── CoplayDev MCP ◄── (ws: ack + id) ◄── Unity
```

State writes are best-effort; the Editor is the source of truth for scene data. The state dir caches only what the agent needs to recover context after a disconnect.

### Flow 3 — Domain reload (the critical path)

1. Unity compiles C# → domain reload → WebSocket drops.
2. CoplayDev MCP detects the close frame.
3. MCP reads `.harness/state/scene.json` for last-known context.
4. MCP waits for Editor "ready" heartbeat (poll every 500ms, cap 30s).
5. MCP reconnects, then issues a **post-reconnect health probe** — one lightweight tool call (`list_open_scenes` or `ping`).
6. If the probe fails → treat as a failed reconnect → surface via the same path as an MCP crash (Section 7, #2).
7. If the probe succeeds → normal operation resumes; agent tool calls during the gap got `{"reconnecting": true}` and were auto-retried by Claude Code / Cursor.

### Flow 4 — Build (local-only path, no CI tokens)

```
harnessctl build --target Windows64 --local        # or just `harnessctl build`
   ├─ writes .harness/build.lock                    → prevents concurrent builds
   ├─ shells: unity -batchmode -quit -projectPath . -buildTarget Win64
   ├─ tails Unity log to .harness/build.log
   └─ on success: artifacts at Builds/Windows64/
```

`--local` skips GameCI; uses raw `unity -batchmode` so no CI token required.

### Flow 5 — Handoff (end of session)

```
harnessctl stop
   ├─ graceful quit Unity Editor
   ├─ stops cost meter, writes final entry to .harness/cost.log
   ├─ updates PROJECT-STATUS.md  (total tokens, scene summary, last tool)
   └─ user commits PROJECT-STATUS.md + scene diffs
```

`PROJECT-STATUS.md` is the contract deliverable per `docs/07-CONTRACT.md`.

### State locations

| Concern | Lives in | Survives |
|---|---|---|
| Scene data | Unity Editor (asset DB) | Editor restart |
| Agent context | `.harness/state/` | Domain reload, MCP restart, Editor restart |
| License | Unity Hub / `.ulf` file | Machine reboot |
| Build artifacts | `Builds/` | Forever |
| Cost log | `.harness/cost.log` | Forever |
| Handoff doc | `PROJECT-STATUS.md` (committed) | Forever |
| MCP discovery | `.harness/mcp.json` | Regenerated each start |

## 7. Error handling

**Philosophy**
- Auto-restart stateless services (MCP servers, cost meter).
- **Never auto-restart the Unity Editor** — surface the crash and let the user decide, because Editor crashes often leave the scene in an unknown state.
- Fail loud, fail actionable: every error path produces a specific exit code + one-line remediation.

**Detection primitives**
- PID check (fast but lies about hangs).
- Heartbeat file (`.harness/heartbeat/<name>` written every 2s, mtime checked every 5s).
- Log scraping for fatal markers (`Fatal error`, `OOM`, `License: invalid`).
- Lock file (`.harness/lock`, mtime < 5min = concurrent invocation).
- **Soft probe** for the Editor (Section 7 row #11) — periodic cheap MCP call (`list_open_scenes` with a short timeout) catches hung-but-alive Editor.

### Scenarios

| # | Scenario | Detection | Recovery | Notify |
|---|---|---|---|---|
| 1 | Unity domain reload | WS close frame | MCP reads state, waits for Editor ready-heartbeat, reconnects, runs **post-reconnect health probe** | Agent gets `{"reconnecting": true}` during gap |
| 2 | MCP server crash | harnessctl heartbeat check | Exp backoff (1→2→4→…→60s); 5 fails/60s → `failed`, stop retrying | `status` shows red + reason |
| 3 | Unity Editor crash | PID dies OR Editor.log has `Fatal error` | **Do not auto-restart.** Mark `crashed`, surface Editor.log tail | `status` shows red + log path |
| 4 | License failure / Personal-tier cap | Unity refuses second MCP OR `--check-license` non-zero | harnessctl refuses second MCP; exit code 75 | Message: "Unity Personal = 1 concurrent MCP. Upgrade to Pro, or stop other MCPs." |
| 5 | Build failure | `game-ci` or `unity -batchmode` exits non-zero | Tail log to `.harness/build.log`; preserve | harnessctl exits with Unity's code + log path |
| 6 | Kenny pack missing | Setup script + `status` check `KENNEY_ASSETS_PATH` symlink target | setup.sh prompts; `status` flags non-fatal | "asset-pack: missing" with remediation |
| 7 | File-IPC corruption | JSON parse error | Quarantine to `.harness/state/quarantine/<ts>-<name>`; continue with empty state | Log warning + quarantined count |
| 8 | Disk full / permission denied | `OSError(28)` / `PermissionError` | Rotate `cost.log` at 10MB; drop non-essential state writes | `doctor` surfaces |
| 9 | Concurrent harnessctl invocations | `.harness/lock` mtime < 5min | Second invocation exits with "another harnessctl is running" | Code 75 |
| 10 | OpenCodex proxy unreachable | MCP can't reach port 10100 | Document setup; supervisor refuses to start dependent MCPs | `status` shows proxy `down` |
| 10a | OpenCodex: proxy up but model failing | Proxy returns 4xx/5xx for the configured model | No auto-recovery (model choice is user's call) | `status` shows `proxy: up, model: failing` + last error line |
| 10b | OpenCodex: proxy up but Codex config stale | `doctor` detects mismatch between Codex's config and proxy | No auto-recovery | `doctor` prints exact `ocx init` / re-inject command |
| 11 | **Editor hung (not crashed)** | Soft probe (`list_open_scenes` with 10s timeout) fails | Mark `editor: hung`; **still refuse auto-restart** | `status` shows `editor: hung` (distinct from `crashed`) + probe latency |
| 12 | `mcp.json` write failure | File-system error during `harnessctl start` write | Treated as non-fatal; log warning; continue with start sequence | `doctor` reports; agent runtime sees its own config-not-found message |

**Exit codes** follow sysexits where applicable: 64 (config), 69 (unavailable), 75 (temp fail), 78 (config error).

**Notification surface**
- `harnessctl status --json` is the canonical machine-readable truth.
- `PROJECT-STATUS.md` is the human/agent paper trail after every successful stop.

**What we deliberately do not do**
- No silent Editor restart.
- No license circumvention.
- No auto-recovery of model choice (user's decision).
- No aggressive Editor hang auto-kill (user decides).

## 8. Testing strategy

### Unit tests (pytest, in `tests/`)

- harnessctl state machine: start/stop/restart transitions, lock-file races.
- File-IPC layer: round-trip JSON write/read; quarantine on corrupt input; rotation behavior.
- License helper: argument parsing, exit code mapping.
- Cost meter parser: each known runtime output format (Claude Code, Codex, OpenCodex).
- `mcp.json` writer: deterministic output; survives Editor still starting.

### Integration tests (mock Editor)

A fake Unity bridge (`tests/mock_unity_bridge.py`) accepts the MCP protocol and simulates:
- Successful tool calls (happy path).
- Domain reload (drops WS, comes back).
- Crash (process exits).
- Hang (accepts WS but stops responding).

Tests run the supervisor against the mock and verify:
- Domain reload recovery + post-reconnect health probe fires.
- MCP crash triggers exp backoff and restart.
- Editor crash does NOT trigger auto-restart.
- Soft probe correctly identifies `hung` vs `crashed`.
- License cap message is surfaced verbatim.

### Smoke tests (`harnessctl doctor`)

Every prerequisite verified before `start`:
- Unity Hub on PATH.
- Unity license (or `.ulf` path).
- `KENNEY_ASSETS_PATH` exists and is readable.
- Git available (submodules).
- OpenCodex (if any MCP depends on it): proxy reachable, configured model returns a 200.

### Manual test scenarios (documented, not automated)

These need a real Unity Editor and are listed in `docs/TESTING.md`:
1. Domain reload during a long Claude Code session → verify file-IPC recovery + post-reconnect probe.
2. Kill CoplayDev MCP via Task Manager → verify exp backoff + restart.
3. Hard-quit Unity Editor → verify `status` shows `crashed`; user can `restart`.
4. Soft-freeze Unity (suspend process) → verify soft probe marks `hung`.
5. Build a 50-script project to Windows64 via `--local`.
6. Run a 30-minute Codex session and inspect `.harness/cost.log`.

## 9. Out of scope

- Headless VPS / cloud deployment (later; documented as future work).
- Godot / Unreal / multi-engine abstraction.
- Multi-user auth, billing, queue, telemetry.
- Web UI for the harness.
- Custom MCP bridge, build runner, or aggregator (all adopted).

## 10. Open questions / future work

1. Should `harnessctl` grow a tiny `tail --follow` subcommand for live log inspection?
2. Should the cost meter emit a Prometheus-style `/metrics` file for a future dashboard?
3. Should we ship a Windows Task Scheduler template for "auto-start harness on login" (optional, off by default)?
4. Can we vendor a tiny in-process WebSocket server (e.g. `websockets` Python lib) to make the post-reconnect probe even cheaper?

## 11. Decisions log

| Decision | Rationale |
|---|---|
| Native processes, no Docker | Windows 11 local-only; Docker adds licensing + setup friction. |
| CoplayDev/unity-mcp primary | Most popular, MIT, ~47 tools. CoderGamester as documented backup. |
| File-IPC for domain reload survival | #1 documented failure mode; unity-ai-bridge reference pattern. |
| Never auto-restart Editor | Hides real bugs and may corrupt scene state. |
| License helper documents caps honestly | Personal tier = 1 concurrent MCP is Unity policy, not a bug. |
| `--local` build flag | Daily iteration shouldn't require CI tokens. |
| Env var for Kenny path | Kit stays portable if the pack moves. |
| GitLab mirror | User's explicit hosting requirement. |