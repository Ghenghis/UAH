#!/usr/bin/env bash
# tests/test_setup_script.sh — verifies setup.sh validates preconditions.
set -euo pipefail

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

# Mock environment
export KENNEY_ASSETS_PATH="$TMP/fake-kenny"
mkdir -p "$KENNEY_ASSETS_PATH"

# Run setup.sh against an empty project; it should succeed and create the symlink
bash "$(dirname "$0")/../scripts/setup.sh" "$TMP/test-project" 2>&1 | tee "$TMP/out.log"

# Verify symlink was created before using test -L
if ! test -L "$TMP/test-project/Assets/_Imported"; then
    echo "FAIL: Assets/_Imported is not a symlink" >&2
    exit 1
fi

# Verify PROJECT-STATUS.md was written
test -f "$TMP/test-project/PROJECT-STATUS.md"

# Re-run; must be idempotent
bash "$(dirname "$0")/../scripts/setup.sh" "$TMP/test-project" >/dev/null 2>&1
echo "OK: setup.sh idempotent"
