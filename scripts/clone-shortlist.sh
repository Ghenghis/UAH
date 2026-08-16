#!/usr/bin/env bash
# Clone the recommended shortlist into a tools/ directory.
# Run from the root of your future Unity project or a parent folder.

set -euo pipefail

TOOLS_DIR="${1:-./tools}"
mkdir -p "$TOOLS_DIR"
cd "$TOOLS_DIR"

echo "Cloning Tier 1 + useful Tier 2 repos into $TOOLS_DIR ..."

# Primary MCP
if [ ! -d "unity-mcp" ]; then
  git clone --depth 1 https://github.com/CoplayDev/unity-mcp.git
else
  echo "unity-mcp already present"
fi

# Strong CLI alternative
if [ ! -d "unityctl" ]; then
  git clone --depth 1 https://github.com/Jason-hub-star/unityctl.git
else
  echo "unityctl already present"
fi

# Alternative high-tool-count MCP
if [ ! -d "Unity-MCP" ]; then
  git clone --depth 1 https://github.com/IvanMurzak/Unity-MCP.git
else
  echo "Unity-MCP already present"
fi

# Optional ComfyUI MCP (uncomment if needed)
# if [ ! -d "comfyui-mcp" ]; then
#   git clone --depth 1 https://github.com/BiodigitalJaz/comfyui-mcp.git
# fi

echo "Done. Review each repo's README for the exact install method (UPM git URL is preferred for most)."
