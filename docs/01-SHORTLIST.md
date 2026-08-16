# 01 – Shortlist of Repositories (core pieces)

Use these first. They are the highest-signal, actively maintained options as of mid-2026.

## Tier 1 – Required for Minimal Viable Pipeline

1. **CoplayDev/unity-mcp**  
   https://github.com/CoplayDev/unity-mcp  
   Primary MCP bridge. ~47 focused tools. Scene, GameObject, asset, script, test, and build control. MIT. Works with Claude Desktop, Cursor, VS Code, local clients. Install via UPM git URL or OpenUPM.

2. **Unity CLI (official)**  
   Install the standalone `unity` binary from Unity.  
   Companion experimental package: `com.unity.pipeline`.  
   Gives terminal / agent control of editor installs, project open, and live Editor commands. Essential for headless and CI-style work.

3. **game-ci/cli** (and optionally orchestrator)  
   https://github.com/game-ci/cli  
   Cross-platform build / test / deploy CLI with Unity plugin support. Pairs well with the official Unity CLI for actual player builds.

## Tier 1.5 – High-Leverage Agent Layer (Strongly Recommended)

4. **OpenCodex (opencodex)**  
   https://github.com/lidge-jun/opencodex  
   npm package: `@bitkyc08/opencodex`  
   Local proxy that lets the official Codex CLI / App / SDK **and** Claude Code run against any LLM (Claude, Grok/xAI, Gemini, DeepSeek, local Ollama, etc.).  
   This is one of the highest-leverage additions: you keep the familiar Codex interface while using your preferred or local models for the entire harness workflow.  
   Full details in `docs/08-OPENCODEX.md`.

## Tier 2 – Strong Alternatives / Complements

5. **Jason-hub-star/unityctl**  
   https://github.com/Jason-hub-star/unityctl  
   170+ CLI commands + MCP tools, validation, rollback, structured JSON. Excellent if you want a more agent-oriented control plane than the official CLI alone.

6. **IvanMurzak/Unity-MCP**  
   https://github.com/IvanMurzak/Unity-MCP  
   High tool count, runtime support, good skill generation. Use if CoplayDev has a gap for your workflow.

## Tier 3 – Optional Asset Generation (Local GPU)

7. **BiodigitalJaz/comfyui-mcp** (or current best ComfyUI MCP)  
   https://github.com/BiodigitalJaz/comfyui-mcp  
   MCP server that talks to a local ComfyUI instance and can drop results into Unity asset folders.

8. **Amin-HP/Unity-ComfyUI-Bridge**  
   https://github.com/Amin-HP/Unity-ComfyUI-Bridge  
   Runtime-friendly bridge for image / audio / 3D generation from ComfyUI workflows.

## Supporting

9. **game-ci** ecosystem (unity-builder actions, Docker images) if you want GitHub/GitLab CI later.  
   https://github.com/game-ci

## Notes for the Agent

- Start with CoplayDev/unity-mcp + official Unity CLI. Only add the others when you hit a concrete limitation.
- OpenCodex is the fastest way to run the whole plan with local or non-OpenAI models while still using Codex / Claude Code tooling.
- Check the latest release tags / main branch activity before pinning.
- Prefer git submodules or a simple `scripts/clone-shortlist.sh` over vendoring the full source trees.
- All of the above are compatible with an existing asset folder (Kenny or custom). No need to generate art on day one.
