# 07 – Harness Contract (for the AI Agent)

You are operating under this contract when using the Unity AI Harness Kit.

## Non-Negotiables

1. Prefer stitching existing repositories over writing new core infrastructure.
2. The minimal viable product is: Unity project + one working MCP server + ability to import and place assets + a documented build path.
3. Do not expand scope into full game design, complex networking, or multiplayer unless the user explicitly asks after the harness is working.
4. Record every important decision and version pin in PROJECT-STATUS.md.
5. If a tool fails, diagnose with the validation steps before replacing it.
6. Keep all generated or temporary files out of the main Assets tree unless they belong there.
7. Respect the licenses of every cloned repository.

## Allowed Freedom

- Choose between CoplayDev, unityctl, or IvanMurzak as the primary MCP based on which one connects cleanly on the user’s machine.
- Add thin wrapper scripts or config files.
- Suggest small C# helpers only when they unblock the agent.
- Use Docker for ComfyUI or MCP servers if it simplifies the environment.

## Success Definition

The harness is complete when a subsequent AI session can open the project, talk to the MCP, place objects from the asset pack, and trigger a build without the human having to re-explain the setup.

Hand control back to the user with a clear PROJECT-STATUS.md and the next logical prompt.
