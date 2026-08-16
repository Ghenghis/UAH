# 02 – Target Folder Structure

Create this layout (or as close as practical) so every piece has a predictable home.

```
unity-ai-project/                  # root of the working project
├── .gitmodules                    # if using submodules
├── .harness/                      # harnessctl's state dir (gitignored except for config)
│   ├── state/                     # file-IPC state (survives domain reload)
│   ├── heartbeat/                 # per-process heartbeat files
│   ├── logs/                      # .harness/<service>.log per process
│   ├── cost.log                   # token spend log
│   ├── build.log                  # last build output
│   ├── config.json                # enabled MCPs (persisted across restarts)
│   ├── mcp.json                   # MCP client config for agent runtimes (regenerated)
│   ├── quarantine/                # corrupt state files quarantined here
│   └── lock                       # concurrent-invocation lock
├── README.md                      # project-specific notes
├── Assets/
│   ├── _Imported/                 # symlink to $KENNEY_ASSETS_PATH (Kenny or user assets)
│   ├── Generated/                 # ComfyUI output lands here (optional)
│   ├── Scripts/
│   ├── Scenes/
│   └── ...
├── Packages/
│   └── manifest.json              # will reference the MCP package
├── ProjectSettings/
├── tools/                         # local clones or symlinks to the shortlist (submodules)
│   ├── unity-mcp/                 # CoplayDev/unity-mcp
│   ├── unity-ai-bridge/           # reference for file-IPC pattern
│   └── game-ci/                   # build runner
├── configs/
│   ├── mcp.json.example           # example client config
│   └── env.example                # example env (KENNEY_ASSETS_PATH, OPENCODEX_PORT, …)
├── scripts/
│   ├── clone-shortlist.sh         # idempotent submodule clone
│   ├── setup.sh                   # one-time install (Phase 0.5)
│   ├── mirror-to-gitlab.sh        # mirror kit repo to GitLab remote
│   ├── harnessctl.py              # the supervisor (start/stop/status/...)
│   └── validate.sh                # smoke test (calls `harnessctl doctor`)
└── docs/                          # copy of this kit's docs or links
    └── superpowers/
        └── specs/                 # design specs (e.g. local-mode)
```

## Why this layout

- `Assets/_Imported` keeps third-party / purchased / free packs separate from generated or hand-authored content. It is a **symlink** to `$KENNEY_ASSETS_PATH`, not a copy — see `05-ASSETS.md`.
- `tools/` keeps the automation repos visible and version-controllable without polluting the Unity Assets folder.
- `.harness/` is harnessctl's private state dir. Everything in `.harness/state/`, `.harness/heartbeat/`, `.harness/logs/`, and `.harness/quarantine/` is regenerated; only `.harness/config.json` is user-edited and worth committing.
- `Configs and scripts stay at the root so any agent can find them without hunting.

## Alternative: Flat + Submodules

If you prefer a pure monorepo style:

```
.
├── external/
│   ├── CoplayDev-unity-mcp/
│   ├── Jason-hub-star-unityctl/
│   └── ...
├── UnityProject/
└── harness/                       # this kit lives here
```

Either works. Prefer the first layout for simplicity when handing off to an agent.
