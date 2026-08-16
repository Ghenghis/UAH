# 00 – START HERE (Agent Entry Point)

Read this file first, then the rest of the docs in numerical order.

## Mission

Assemble a working Unity + AI control pipeline by **stitching existing open-source repositories**, supervised by `harnessctl`. Do not write a new MCP server or CLI from scratch unless a critical gap is proven after testing the shortlist.

## Vision

The kit is **local-first** by default: native Windows 11 processes, no Docker, one Unity project at a time, solo operator. See [`../VISION.md`](../VISION.md) for the full mission and constraints, and [`superpowers/specs/2026-08-15-unity-ai-harness-local-design.md`](superpowers/specs/2026-08-15-unity-ai-harness-local-design.md) for the full local-mode design spec.

## Constraints

- Prefer MIT / Apache-2.0 / public-domain tools.
- Keep the surface area small. **One primary MCP server + Unity CLI + `harnessctl` supervisor is enough for the minimal viable product.**
- User already has (or will supply) a local asset folder. Treat asset generation as optional.
- Target Unity 2022.3 LTS or Unity 6.x. Prefer Unity 6 if the machine has it.
- Default host is **Windows 11** with Unity installed via Hub. VPS / headless mode is future work.
- The final deliverable is a project the user can open and an agent can continue to drive — with `PROJECT-STATUS.md` as the handoff contract.

## Recommended Reading Order

1. This file
2. `01-SHORTLIST.md` – exact repos to use (now mostly adopted wholesale)
3. `02-FOLDER-STRUCTURE.md` – target layout (includes `.harness/` for state)
4. `03-ACTION-PLAN.md` – step-by-step execution (phases 0-7 + local-harness phase)
5. `04-MCP-AND-CLI-NOTES.md` – connection and validation tips (includes domain-reload survival)
6. `05-ASSETS.md` – how to bring in Kenny or local packs (`KENNEY_ASSETS_PATH` env var)
7. `06-OPTIONAL-COMFYUI.md` – only if generation is desired (gated behind `harnessctl enable comfyui`)
8. `08-OPENCODEX.md` – strongly recommended; run Codex / Claude Code on any model (local or cloud)
9. `superpowers/specs/2026-08-15-unity-ai-harness-local-design.md` – full design spec for local mode

Then execute `03-ACTION-PLAN.md`.

## Primary Success Path (Minimal, with `harnessctl`)

1. Set `KENNEY_ASSETS_PATH` to your asset pack (or accept the default).
2. Run `bash scripts/setup.sh` — clones submodules, installs the UPM MCP package, symlinks assets, writes `PROJECT-STATUS.md`.
3. Run `harnessctl license activate` — one-time Unity license setup.
4. Run `harnessctl start` — brings up Unity Editor + primary MCP + cost meter; writes `.harness/mcp.json`.
5. Open your AI agent runtime (Claude Code / Cursor / Codex / OpenCodex); it discovers `.harness/mcp.json` and connects.
6. Use `harnessctl doctor` to validate at any time.
7. End the session with `harnessctl stop`; commit the updated `PROJECT-STATUS.md`.

Everything else is enhancement. OpenCodex is the highest-leverage next step for model flexibility.
