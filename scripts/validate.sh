#!/usr/bin/env bash
# Simple sanity checks an agent can run after setup.
# Expand as needed once the project path is known.

set -euo pipefail

echo "=== Unity AI Harness – basic validation ==="

if command -v unity >/dev/null 2>&1; then
  echo "[OK] unity CLI is on PATH"
  unity --version || true
else
  echo "[WARN] unity CLI not found on PATH – locate the binary manually"
fi

if command -v git >/dev/null 2>&1; then
  echo "[OK] git is available"
else
  echo "[FAIL] git is required"
  exit 1
fi

echo "Next: open Unity, install the MCP package, and test a simple tool call from your MCP client."
echo "See docs/03-ACTION-PLAN.md and docs/04-MCP-AND-CLI-NOTES.md"
