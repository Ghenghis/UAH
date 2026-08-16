# Unity AI Harness Kit

**Purpose**: A self-hosted, local-first kit that turns a Windows 11 machine into a Unity AI development pipeline. A single command (`harnessctl start`) brings up the Editor + MCP servers; an AI agent (Claude Code / Cursor / Codex / OpenCodex) drives the rest; the failure modes that bite every Unity MCP setup are already handled.

This is **not** a from-scratch engine. It is a contract + structure + shortlist of mature repos + a thin-glue supervisor (`harnessctl`) so the agent can stitch, configure, and drive Unity + optional local ComfyUI asset generation + builds with minimal human babysitting.

See **[VISION.md](VISION.md)** for the complete picture (mission, constraints, what we build vs adopt, non-goals) and **[docs/superpowers/specs/2026-08-15-unity-ai-harness-local-design.md](docs/superpowers/specs/2026-08-15-unity-ai-harness-local-design.md)** for the full architecture.

**Default assumption**: You already have (or will drop in) a folder of game assets. Kenny Game Assets All-in-1 is the recommended free/commercial-friendly starting pack if you need one. Generation via ComfyUI is optional.

**Goal of the kit**: Get from "empty folder + assets + Unity on the box" → `harnessctl start` → agent-controllable scenes/scripts → optional generated art → testable build (no CI tokens needed) in as few steps as possible.

## Quick Start for the Human

1. Unzip this kit.
2. Set `KENNEY_ASSETS_PATH` to your asset pack (or accept the default path).
3. Run `bash scripts/setup.sh` once — clones submodules, installs the UPM MCP package, symlinks assets, writes `PROJECT-STATUS.md`.
4. Run `harnessctl start` — brings up Unity Editor + MCP servers + cost meter; writes `.harness/mcp.json` for the agent to discover.
5. Open your AI agent runtime (Claude Code / Cursor / Codex / OpenCodex) and let it connect via the `.harness/mcp.json` config.
6. Follow the prompts in `/prompts` or use your own.

## What This Kit Contains

- `VISION.md` – the complete mission + constraints + non-goals
- `docs/` – Ordered reading list, contracts, MCP + CLI notes, OpenCodex details
- `docs/superpowers/specs/` – The full local-mode design spec (architecture, components, error model)
- `configs/` – Example mcp.json, environment templates
- `scripts/` – Clone / setup / mirror helpers (`scripts/setup.sh`, `scripts/clone-shortlist.sh`, `scripts/mirror-to-gitlab.sh`)
- `prompts/` – Ready-to-paste system and task prompts for different AI tools
- `examples/` – Minimal folder layout target + `PROJECT-STATUS.template.md`

**OpenCodex is now included (Tier 1.5).**  
It lets you run the official Codex CLI/App/SDK and Claude Code against any model — including your local ones. This is one of the highest-leverage additions for cost, privacy, and model choice while still using the tools you already planned to hand the kit to.

## Hosting

This kit is mirrored to **both GitHub and GitLab**. `scripts/mirror-to-gitlab.sh` pushes to the configured GitLab remote after every `git push` to the GitHub one.

## License Note

All recommended upstream projects are MIT or similarly permissive. This kit itself is released as CC0 / public domain for the documentation and glue. Respect the licenses of the individual repos you clone.

## Success Criteria for the Agent

A successful run of this kit produces:
- A Unity project that opens cleanly
- `harnessctl start` brings up the Editor + primary MCP without errors
- At least one MCP server connected and responding
- Ability for the agent to create GameObjects, edit simple scripts, and import assets from a designated folder
- Domain-reload survival: editing a C# script does not lose agent context (file-IPC state)
- A documented path to build (`harnessctl build --local` for daily iteration, GameCI for CI)
- Optional ComfyUI path that can drop textures into the project (gated behind `harnessctl enable comfyui`)
- OpenCodex running so the same agent can use local or preferred models
- `PROJECT-STATUS.md` written at the end of every session for the next agent run

If any of those fail, the agent should diagnose using `harnessctl doctor` rather than rewriting core tools.
