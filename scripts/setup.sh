#!/usr/bin/env bash
# scripts/setup.sh — Phase 0.5 idempotent install for the Unity AI Harness.
#
# Usage: bash scripts/setup.sh [project_dir]
#   project_dir: optional; defaults to the current directory.
#
# Env:
#   KENNEY_ASSETS_PATH  required (path to asset pack; will be symlinked)
#   UNITY_HUB_PATH      optional
#
# Idempotent: re-running is safe and a no-op if everything is already set up.

set -euo pipefail

PROJECT_DIR="${1:-$PWD}"
KENNEY_ASSETS_PATH="${KENNEY_ASSETS_PATH:-}"

# Prefer python3, fall back to python (the script is also used on Windows).
PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
    echo "ERROR: python/python3 not on PATH (need 3.11+)." >&2
    exit 69
fi

# --- 1. Preconditions -------------------------------------------------------
if [[ -z "$KENNEY_ASSETS_PATH" ]]; then
    echo "ERROR: KENNEY_ASSETS_PATH is not set." >&2
    echo "  Set it to the absolute path of your asset pack, e.g." >&2
    echo "    export KENNEY_ASSETS_PATH='G:\\Github\\Kenney Game Assets All-in-1 3.6.0'" >&2
    exit 64  # EX_USAGE
fi
if [[ ! -d "$KENNEY_ASSETS_PATH" ]]; then
    echo "ERROR: KENNEY_ASSETS_PATH='$KENNEY_ASSETS_PATH' is not a directory." >&2
    exit 64
fi
if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git not on PATH." >&2
    exit 69  # EX_UNAVAILABLE
fi

# --- 2. Submodules ----------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HARNESS_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$HARNESS_ROOT"
git submodule update --init --recursive

# --- 3. Project directory ---------------------------------------------------
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
mkdir -p Assets Packages ProjectSettings .harness/state .harness/heartbeat \
         .harness/logs .harness/quarantine

# --- 4. Symlink Kenny -------------------------------------------------------
if [[ ! -L Assets/_Imported ]]; then
    if ln -s "$KENNEY_ASSETS_PATH" Assets/_Imported 2>/dev/null; then
        echo "Created symlink: Assets/_Imported -> $KENNEY_ASSETS_PATH"
    else
        # Fallback for Windows where unprivileged ln -s often fails.
        "$PYTHON_BIN" - "$KENNEY_ASSETS_PATH" "Assets/_Imported" <<'PY'
import os
import sys
os.symlink(sys.argv[1], sys.argv[2], target_is_directory=True)
PY
        echo "Created symlink (via python): Assets/_Imported -> $KENNEY_ASSETS_PATH"
    fi
else
    echo "Symlink already exists: Assets/_Imported"
fi

# --- 5. UPM manifest entry (only if not present) ----------------------------
if [[ ! -f Packages/manifest.json ]]; then
    cat > Packages/manifest.json <<'JSON'
{
  "dependencies": {
    "com.unity-mcp": "https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity"
  }
}
JSON
    echo "Wrote Packages/manifest.json"
fi

# --- 6. PROJECT-STATUS.md --------------------------------------------------
if [[ ! -f PROJECT-STATUS.md ]]; then
    cp "$HARNESS_ROOT/examples/PROJECT-STATUS.template.md" PROJECT-STATUS.md
    echo "Wrote PROJECT-STATUS.md"
fi

# --- 7. License activation (best-effort, non-fatal) ------------------------
if "$PYTHON_BIN" "$HARNESS_ROOT/scripts/harnessctl.py" license status >/dev/null 2>&1; then
    echo "License: already activated"
else
    echo "License: not activated. Run 'harnessctl license activate' when ready."
fi

echo "Setup complete. Next: 'harnessctl start'."
