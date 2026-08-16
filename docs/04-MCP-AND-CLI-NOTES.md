# 04 – MCP and CLI Notes

## Connecting an MCP Client

Most clients use a JSON config. Example for Claude Desktop / Cursor style:

```json
{
  "mcpServers": {
    "unity": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/CoplayDev/unity-mcp.git", "unity-mcp"],
      "env": {
        "UNITY_PROJECT_PATH": "/absolute/path/to/your/UnityProject"
      }
    }
  }
}
```

Exact command depends on the chosen MCP server. Always prefer the install method documented in the repo’s README (UPM + Window configurator is usually easiest for CoplayDev).

## Validation Commands the Agent Should Know

- Create an empty GameObject named "HarnessTest"
- List the current scene hierarchy
- Create a simple C# MonoBehaviour and attach it
- Refresh the Asset Database after dropping new files into Assets/
- Capture a screenshot of the Game view if the tool exists

If any of these fail, check:
1. Is the Unity Editor actually running?
2. Is the MCP bridge window showing “connected”?
3. Are there console errors about domain reloads or missing assemblies?

## Unity CLI Basics

```bash
# List installed editors
unity editors --format json

# Open a project
unity open /path/to/project

# With the pipeline package installed, agents can call custom [CliCommand] methods
```

Prefer structured JSON output wherever the CLI supports it so the agent can parse results reliably.

## Common Pitfalls

- **Domain reloads drop WebSocket connections** — this is the #1 documented failure mode. The kit handles it via a file-IPC layer in `.harness/state/`: the MCP server reads sidecar JSON on reconnect and resumes with context intact. After reconnect, it issues a lightweight health probe (`list_open_scenes` or `ping`); if that fails, the reconnect is treated like a fresh MCP crash.
- Multiple Unity instances: most MCP servers need an explicit project path or instance selector.
- Path separators on Windows vs WSL – always use absolute paths and normalize them.

## MCP discovery (`harnessctl start` writes this)

After `harnessctl start`, the agent runtime finds MCP endpoints at:

```
.harness/mcp.json
```

Shape (Claude Desktop / Cursor / Claude Code / Codex / OpenCodex all consume this):

```json
{
  "mcpServers": {
    "unity": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/CoplayDev/unity-mcp.git", "unity-mcp"],
      "env": {
        "UNITY_PROJECT_PATH": "<absolute path>",
        "HARNESS_STATE_DIR": "<absolute path to .harness/state>"
      }
    }
  }
}
```

The file is regenerated on every `harnessctl start` and on `harnessctl enable/disable`. If it is missing or unreadable, `harnessctl doctor` flags it; the start sequence itself does not block on a successful write (the file is regenerated next start anyway).
