#!/usr/bin/env bash
# scripts/mirror-to-gitlab.sh — push current branch to the `gitlab` remote.
#
# Run after `git push origin <branch>` to keep GitHub and GitLab in sync.
# Failures are non-fatal; the user re-runs after resolving auth/network issues.

set -euo pipefail

if ! git remote get-url gitlab >/dev/null 2>&1; then
    echo "ERROR: no 'gitlab' remote configured." >&2
    echo "  Add one with: git remote add gitlab <your-gitlab-url>" >&2
    exit 64
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push gitlab "$BRANCH"
