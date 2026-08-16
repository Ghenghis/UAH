# Unity AI Harness — Upgrade Action Plan

This plan organizes the next phases of the project as numbered milestones. Each milestone is broken into sections; each section gets its own branch, commit, and push.

> Execution rules: `docs/UPGRADE_CONTRACT.md` is the source of truth for branch names, commit messages, and quality gates.

## Current baseline

- `master` holds the M4 implementation from `docs/superpowers/plans/2026-08-15-unity-ai-harness-local.md`.
- `release/snapshot` holds a packaged snapshot of M4.
- `upgrades` is the staging branch for M5 work.

## M5 — CI/CD, packaging, and code quality

Goal: make the harness installable, testable in CI, and safe to iterate on.

| Section | Branch | Work | Acceptance |
|---------|--------|------|------------|
| M5.1 | `feature/pyproject-packaging` | Add `pyproject.toml` so `pip install -e .` and `uv pip install -e .` work; expose `harnessctl` as a console script. | `harnessctl --version` works from a fresh venv. |
| M5.2 | `feature/windows-setup` | Create `scripts/setup.ps1` equivalent of `scripts/setup.sh` and a `setup.cmd` shim. | `tests/test_setup_script.ps1` passes. |
| M5.3 | `feature/lint-and-format` | Add `ruff` and `black` (or `ruff format`) to `pyproject.toml`; add `pre-commit` config. | `ruff check .` and `ruff format --check .` pass on CI. |
| M5.4 | `feature/github-actions` | Add `.github/workflows/ci.yml` that runs `pytest`, `ruff`, and the bash smoke tests on Windows. | All jobs green on a PR. |
| M5.5 | `feature/harnessctl-upgrade` | Add `harnessctl upgrade` that runs `git pull` and re-installs itself. | `harnessctl upgrade --dry-run` reports what it would do. |

Release: merge M5 sections into `upgrades`, then open `release/v0.5.0` → `master`, tag `v0.5.0`.

## M6 — Operator experience and observability

Goal: reduce friction for the developer running the harness daily.

| Section | Branch | Work | Acceptance |
|---------|--------|------|------------|
| M6.1 | `feature/harnessctl-config` | Add `harnessctl config get/set` for safe editing of `mcp.json` and `.harness/config.json`. | Tests in `tests/test_harnessctl_config.py` pass. |
| M6.2 | `feature/harnessctl-logs` | Add `harnessctl logs [--tail]` to surface `.harness/logs/*.log`. | `harnessctl logs --tail` streams a test log. |
| M6.3 | `feature/doctor-improvements` | Extend `harnessctl doctor` to detect Unity Hub, python, uv, and docker. | `harnessctl doctor --json` reports all checks. |
| M6.4 | `feature/cost-meter-loop` | Promote the cost meter from a start hook to a real daemon thread with an HTTP sink. | `.harness/cost.log` gets one entry per turn. |

Release: `release/v0.6.0` → `master`, tag `v0.6.0`.

## M7+ — Deferred / out of scope

These are documented but not scheduled. Re-evaluate after M6.

- VPS / headless deployment (Kasm / noVNC)
- Multi-engine abstraction (Godot / Unreal)
- Multi-user auth / SaaS layer
- Web UI for `harnessctl status`

## How to follow this plan

1. `git checkout upgrades`
2. `git checkout -b feature/<section-name>`
3. Do the work, one logical section per commit.
4. Run the acceptance check.
5. `git push origin feature/<section-name>`
6. Open a PR to `upgrades`.
7. After merge, delete the feature branch.
8. When the milestone is done, cut `release/v<x>.<y>.0` from `upgrades`, stabilize, then PR to `master` and tag.
