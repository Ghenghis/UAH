# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `docs/UPGRADE_CONTRACT.md` — branching, commit, and release convention for the project.
- `docs/UPGRADE_PLAN.md` — milestone-driven upgrade action plan.
- Project website at `docs/website/`.
- README Releases section pointing at the packaged GitHub Release (not a zip in-tree).

## [0.4.0] — 2026-08-16

### Added

- `harnessctl` CLI with `start`, `stop`, `status`, `restart`, `build --local`, `doctor`, `license`, `enable`, `disable`, and `setup`.
- File-IPC state layer with quarantine and stale detection (`scripts/file_ipc.py`).
- Heartbeat monitoring for the Unity Editor and primary MCP (`scripts/heartbeat.py`).
- Domain-reload reconnect with health probes (`scripts/reconnect.py`).
- MCP config writer (`scripts/mcp_config_writer.py`) and cost meter parsers (`scripts/cost_meter.py`).
- Setup script with Windows symlink fallback (`scripts/setup.sh`).
- GitLab mirror script (`scripts/mirror-to-gitlab.sh`).
- Mock Unity bridge and integration tests for reload/crash/hang scenarios.
- Manual test runbook (`docs/TESTING.md`).

### Fixed

- Broken `minimax` MCP server by constraining the `uvx` invocation to `mcp<2.0`.

## [0.1.0] — 2026-08-15

### Added

- Initial repo skeleton: `VISION.md`, `.gitmodules`, `env.example`, and core documentation.
