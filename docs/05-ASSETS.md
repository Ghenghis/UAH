# 05 – Assets Strategy

## Default Recommendation

Use **Kenny Game Assets All-in-1** if the user does not already have a preferred pack.

- itch.io page: https://kenney.itch.io/kenney-game-assets-all-in-1
- ~60,000+ assets (2D, 3D, UI, audio, fonts)
- Coherent style
- Commercial use allowed, no attribution required
- Pay-what-you-want (minimum currently around $20, free updates for life)
- Includes a launcher for Windows/Linux

If the user already has assets (their own, other itch packs, Unity Asset Store, etc.), simply drop them into `Assets/_Imported/` and proceed. Do not force Kenny.

## Import Workflow for the Agent

1. Create `Assets/_Imported/` if it does not exist.
2. Copy or move the asset root into that folder (or a dated subfolder).
3. Let Unity finish importing.
4. Search the Project window for a few known good prefabs / sprites / models.
5. Instantiate 3–5 of them in a new scene, arrange them, and save the scene as `Assets/Scenes/HarnessDemo.unity`.
6. Record in PROJECT-STATUS.md which specific assets were used so later sessions stay consistent.

## Generated Assets

If ComfyUI is active, route all new files into `Assets/Generated/` with a clear naming convention (date + prompt hash or sequential). Never overwrite `_Imported`.

## License Hygiene

Keep a simple `Assets/_Imported/SOURCES.md` that lists the origin of each pack. This protects the user later if the project is shared or published.
