#!/usr/bin/env bash
# tests/test_mirror.sh — verifies mirror-to-gitlab.sh pushes to a local "gitlab" bare repo.
set -euo pipefail

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

# Local bare repo stands in for GitLab.
git init --bare "$TMP/gitlab.git" >/dev/null

# Source repo with the mirror script and a remote named `gitlab`.
mkdir "$TMP/src" && cd "$TMP/src"
git init -q
git -C . remote add gitlab "$TMP/gitlab.git"
mkdir -p scripts
cp "$OLDPWD/scripts/mirror-to-gitlab.sh" scripts/
chmod +x scripts/mirror-to-gitlab.sh
git add scripts/mirror-to-gitlab.sh
git -c user.email=test@x -c user.name=test commit -qm "add mirror script"

bash scripts/mirror-to-gitlab.sh >/dev/null

git --git-dir="$TMP/gitlab.git" log --oneline | grep -q "add mirror script"
echo "OK: mirror-to-gitlab.sh pushes to gitlab remote"
