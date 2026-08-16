# 06 – Optional ComfyUI Integration

Only pursue this path if the user explicitly wants generated art or the existing asset pack is insufficient.

## Prerequisites

- Local ComfyUI running (default http://127.0.0.1:8188)
- A working checkpoint / workflow the user already trusts
- Sufficient VRAM (user’s RTX 3090 Ti class hardware is more than enough)

## Recommended Order

1. Confirm ComfyUI is healthy with a simple txt2img.
2. Install a ComfyUI MCP server (BiodigitalJaz/comfyui-mcp or current best equivalent).
3. Configure the MCP so it can write finished PNGs directly into the Unity project’s `Assets/Generated/` folder.
4. Test one generation → import → material assignment cycle.
5. Optionally install Amin-HP/Unity-ComfyUI-Bridge if runtime generation inside a built player is desired later.

## Agent Rules for Generation

- Always generate at a resolution and format that Unity can import cleanly (power-of-two preferred, PNG).
- Prefer img2img or ControlNet when the user already has a style reference from the Kenny pack.
- Never generate content that would violate the user’s stated constraints.
- Log every generation prompt and seed in a simple text file next to the output.

If the MCP or bridge proves unstable, fall back to manual export from ComfyUI and a simple “watch folder” import script. Do not block the whole pipeline on generation.
