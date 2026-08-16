# Vision — Unity AI Harness

A self-hosted, local-first kit that turns a Windows 11 machine into a Unity AI development pipeline. One command to start, an agent (Claude Code / Cursor / Codex / OpenCodex) drives the rest, and the failure modes that bite every Unity MCP setup are already handled.

## Who it's for

A solo developer (or small team) who wants the AI-driven game-dev capability of products like Seele.ai, but **without the SaaS, vendor lock-in, or recurring cost**. They have (or will install) Unity 2022.3 LTS / Unity 6.x on their own machine and want their agent runtime to talk to a real Editor — with assets already on disk.

## Core constraints

| | |
|---|---|
| **Host** | Local Windows 11 (no VPS required; VPS optional later) |
| **Operator** | Solo — no multi-tenancy, no auth, no billing |
| **Engine** | Unity only — Godot / Unreal are out of scope |
| **Projects** | One at a time |
| **Form factor** | Native processes — no Docker, no containers, no web UI |
| **Agent runtime** | Bring your own — Claude Code, Cursor, Codex, OpenCodex, anything that speaks MCP |
| **Default asset input** | [Kenny Game Assets All-in-1](https://kenney.itch.io/kenney-game-assets-all-in-1) v3.6.0 (driven by `KENNEY_ASSETS_PATH`) |
| **Model** | Bring your own — local Ollama, Claude, Grok, Gemini, DeepSeek, anything OpenCodex fronts |

## Method

**Stitch, don't invent.** Every layer that has a mature open-source replacement is adopted wholesale. New code is only written where no good alternative exists.

**Adopted wholesale (no work for the kit):**
- `CoplayDev/unity-mcp` — primary MCP bridge (~47 tools, MIT)
- `game-ci/cli` + `unity-builder` — build runner (MIT, GitHub + GitLab examples)
- `butterlatte-zhang/unity-ai-bridge` — reference for file-IPC pattern
- `OpenCodex` — model flexibility proxy

**Built by the kit (the actual value):**
- `harnessctl` — supervisor for the Editor + MCPs + cost meter
- File-IPC state layer — survives Unity domain reloads (the #1 documented failure mode)
- License helper — honest wrapper that documents Unity Personal-tier limits
- Cost meter — token spend per agent session (no OSS project does this)
- Setup script + GitLab mirror — one-shot install and dual-host mirror
- Updated docs (this kit) — local-mode path documented end-to-end

## Non-goals

We deliberately do **not** build:
- Multi-tenant / SaaS layer (no auth, billing, queue, per-user storage)
- Headless VPS deployment (later, if needed)
- Multi-engine abstraction (Godot / Unreal / etc.)
- MCP bridge, build runner, or aggregator from scratch (solved layers — adopted instead)
- Web UI, noVNC, Kasm, webtop — would pull GPL-3.0 license contamination
- Custom license circumvention — Unity Personal caps are policy, not bugs

## What success looks like

A user with a fresh Windows 11 box, Kenny pack on disk, and Claude Code installed:

1. Clones this kit.
2. Runs `bash scripts/setup.sh` once.
3. Runs `harnessctl start`.
4. Claude Code picks up `.harness/mcp.json`, connects to the Editor, and starts working.
5. The user can edit C# in Unity, triggering domain reloads, without losing the agent's context.
6. `harnessctl build --target Windows64 --local` ships a build with no CI tokens required.
7. `PROJECT-STATUS.md` captures the session for the next agent run.

## Design spec

The full architecture, components, data flow, and error model live in:
[`docs/superpowers/specs/2026-08-15-unity-ai-harness-local-design.md`](docs/superpowers/specs/2026-08-15-unity-ai-harness-local-design.md)