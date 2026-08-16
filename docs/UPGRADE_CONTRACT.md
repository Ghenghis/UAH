# Unity AI Harness — Upgrade & Release Contract

This contract defines the branching, commit, and release discipline used to evolve the Unity AI Harness. It is derived from the GitFlow, Release Flow, and Conventional Commits patterns and is tailored for a single-maintainer / small-team, versioned desktop tool.

## 1. Branch Model (Release Flow / lightweight GitFlow)

We keep a **single trunk** (`master`) and use **short-lived feature/release branches**. No long-lived `develop` branch is required at this scale, but `upgrades` is an integration branch where multiple in-flight enhancements can be staged before merging to `master`.

| Branch | Purpose | Base | Merge target |
|--------|---------|------|--------------|
| `master` | Always-shippable, tested code. Tagged releases live here. | — | — |
| `upgrades` | Staging branch for the next enhancement/upgrade cycle. | `master` | `master` (via PR) |
| `feature/<name>` | One logical upgrade or feature. | `upgrades` | `upgrades` (via PR) |
| `release/<version>` | Stabilization for a numbered release. | `upgrades` or `master` | `master` and back-merge to `upgrades` |
| `hotfix/<name>` | Urgent fix against a release tag. | `master` or `release/<version>` | `master` and `upgrades` |

## 2. Commit Convention

All commits follow [Conventional Commits](https://www.conventionalcommits.org/) so the history is machine-readable and can drive changelogs and SemVer.

Allowed types (with examples for this project):

- `feat` — new harness capability (e.g., new `harnessctl` subcommand)
- `fix` — bug fix in `harnessctl`, MCP bridge, or tests
- `perf` — performance improvement (faster heartbeats, smaller JSON writes)
- `refactor` — non-behavioral code reorganization
- `docs` — Markdown, README, TESTING, or contract changes
- `test` — test-only changes
- `build` — `setup.sh`, `pyproject.toml`, or packaging changes
- `ci` — GitHub Actions, GitLab CI, or validation scripts
- `chore` — maintenance, dependency bumps, cleanup
- `revert` — reverts a previous commit

Upgrade-specific scopes (optional but encouraged):

- `(harnessctl)`
- `(mcp)`
- `(unity)`
- `(ipc)`
- `(tests)`
- `(docs)`
- `(ci)`

Examples:

```text
feat(harnessctl): add enable/disable for optional MCPs
fix(heartbeat): treat hangs as distinct from crashes
chore(deps): bump mcp pin to <2.0 in windsurf config
docs(contract): add upgrade and release contract
```

## 3. Section-by-Section Commit & Push Rules

An upgrade is broken into **small, independently mergeable sections**:

1. One logical section per commit.
2. Each section must have a green local run:
   - `python -m pytest tests/ -v`
   - `bash tests/test_setup_script.sh`
   - `bash tests/test_mirror.sh`
   - `harnessctl doctor` for manual pre-flight when a real Unity Editor is present
3. Push the section before starting the next one.
4. Never force-push to `master` or `upgrades`.
5. Keep each `feature/*` branch focused on one upgrade goal; delete it after merge.

## 4. Quality Gates

A section may be merged only when:

- All tests pass.
- New behavior has a test (or a manual scenario in `docs/TESTING.md` if it requires Unity).
- Documentation is updated if the user-facing surface changes.
- Commit history is clean and follows Conventional Commits.

## 5. Versioning & Releases

- Use [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.
- Tags are cut from `master` on a `release/*` branch.
- Release notes are derived from Conventional Commit history.
- The `release/snapshot` branch holds packaged or experimental snapshots; it is not the main release train.

## 6. Release Checklist

- [ ] Create `release/<version>` from `upgrades`.
- [ ] Run full test suite and manual runbook.
- [ ] Update `docs/TESTING.md` and `CHANGELOG.md`.
- [ ] Tag `v<version>` on `master` after merge.
- [ ] Delete the `release/<version>` branch after merge.

## 7. References

- Chris Krycho, *A Git Workflow for Managing Long-Running Upgrades* — https://v5.chriskrycho.com/journal/git-workflow-for-managing-long-running-upgrades-a/
- Martin Fowler, *Patterns for Managing Source Code Branches* — https://martinfowler.com/articles/branching-patterns.html
- Conventional Commits — https://www.conventionalcommits.org/en/v1.0.0/
- Trunk Based Development — https://trunkbaseddevelopment.com/
