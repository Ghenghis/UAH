# 03 – Action Plan (Execute in Order)

This is the concrete sequence the agent should follow. Mark each step complete before moving on.

## Phase 0 – Prerequisites Check

- [ ] Unity 2022.3 LTS or Unity 6.x is installed and launchable from the command line.
- [ ] Official Unity CLI (`unity` binary) is on PATH or its full path is known.
- [ ] Git is available.
- [ ] Python 3.11+ is on PATH (for `harnessctl`).
- [ ] A local folder of assets exists. Set `KENNEY_ASSETS_PATH` (e.g. `G:\Github\Kenney Game Assets All-in-1 3.6.0`); the setup script symlinks it into `Assets/_Imported/`.
- [ ] An MCP-capable client is ready (Claude Desktop, Cursor, Claude Code, Codex, OpenCodex).
- [ ] (Strongly recommended) OpenCodex installed so Codex / Claude Code can use any model (local or preferred). See `docs/08-OPENCODEX.md`.

## Phase 0.5 – Local harness setup (run once)

This phase installs the supervisor and validates the kit on the local machine.

1. `git submodule update --init` — clones `unity-mcp`, `game-ci`, `unity-ai-bridge`, `unityctl` into `tools/`.
2. `bash scripts/setup.sh` — installs the UPM MCP package entry in `Packages/manifest.json`, symlinks `$KENNEY_ASSETS_PATH` into `Assets/_Imported/`, writes `PROJECT-STATUS.md`.
3. `harnessctl license activate` — wraps `game-ci/unity-license-activate`. Honest about Personal-tier caps (1 concurrent MCP); prints Pro upgrade path if exceeded.
4. `harnessctl doctor` — verifies Hub, license, asset path, git, optional OpenCodex proxy.
5. (Optional) `harnessctl enable comfyui` — enables the ComfyUI MCP for asset generation.

Phase 0.5 is idempotent — re-run safely at any time.

## Phase 1 – Create or Open Unity Project

1. Create a new 3D (or 2D) URP / Built-in project, or open an existing empty one.
2. Note the absolute path. All later commands will use it.

## Phase 2 – Install Primary MCP

1. In Unity Package Manager → Add package from git URL:  
   `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity`
   (pin a recent tag if desired, e.g. `#v10.0.0` or whatever is current).
2. Open Window → MCP for Unity (or equivalent) and configure the detected clients.
3. Start the Unity Editor so the bridge is running.
4. From the MCP client, run a simple tool (e.g. list scenes or create an empty GameObject) to confirm connectivity.

## Phase 3 – Bring in Assets

1. Copy or symlink the user’s asset pack (or Kenny) into `Assets/_Imported/`.
2. Let Unity import. Fix any missing scripts or materials only if they block basic use.
3. Ask the agent to place 3–5 objects from the pack into a new scene and save it.

## Phase 4 – Optional CLI / unityctl Layer

1. Install or locate the official Unity CLI.
2. (Optional) Clone Jason-hub-star/unityctl and verify it can talk to the same Editor.
3. Write a one-line validation command that the agent can re-run later.

## Phase 5 – Optional ComfyUI Path

Only if generation is wanted:
1. Ensure a local ComfyUI is running on the default port.
2. Install / configure a ComfyUI MCP server.
3. Test generating one texture and importing it into `Assets/Generated/`.

## Phase 6 – Build Path

1. Use Unity CLI or game-ci/cli to produce a simple StandaloneWindows64 (or Linux) build.
2. Confirm the build runs and loads the scene that contains the imported assets.

## Phase 7 – Hand-off Documentation

Write a short `PROJECT-STATUS.md` in the project root that records:
- Which MCP server is active
- Asset source used
- Any version pins
- The exact commands that currently work
- Known limitations

At this point the kit has succeeded. Further game design is outside the harness scope.
