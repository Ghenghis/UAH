# 08 – OpenCodex (Highly Recommended)

**Repo / Install**: https://github.com/lidge-jun/opencodex  
npm: `@bitkyc08/opencodex`  
Site: https://opencodex.me

## Why this is game-changing for the harness

OpenCodex is a local proxy that lets the **official OpenAI Codex CLI / App / SDK** (and Claude Code) talk to **any** model provider — Claude, Grok/xAI, Gemini, DeepSeek, Kimi, local Ollama, OpenRouter, etc. — without forking Codex itself.

For this Unity AI Harness that means:

- You can drive the entire stitching + Unity MCP workflow with your local Qwen / other models or cheaper/better cloud models while still using the Codex interface and tooling you already know.
- Full tool-calling, streaming, and multi-agent support is preserved.
- Privacy and cost control stay in your hands (especially valuable with your local GPU setup).
- One proxy can also feed Claude Code, so the same models are available across the agents you already plan to hand the kit to.

## Quick integration steps for the agent

1. `npm install -g @bitkyc08/opencodex`
2. `ocx init` (or `opencodex init`) — pick providers, set API keys or local endpoints, optionally inject into Codex config.
3. `ocx start` (default port 10100)
4. Run normal `codex "..."` commands; they now route through the proxy.
5. For local models: point a provider at your Ollama / LM Studio OpenAI-compatible endpoint.
6. Document the chosen default model and any sub-agent models in PROJECT-STATUS.md.

## Agent rules when using OpenCodex

- Prefer it when the user wants local or non-OpenAI models for the harness work.
- Keep the proxy running for the duration of long agent sessions.
- If Codex or Claude Code already works for the user without it, OpenCodex is still an optional power-up, not a hard requirement for the minimal path.
- Never hard-code secrets; use environment variables or the dashboard.

## Placement in the kit

Treat OpenCodex as a **Tier-1.5** tooling layer: not required for the absolute minimal Unity + MCP path, but extremely high leverage once the agent starts executing multi-step plans against the project.
