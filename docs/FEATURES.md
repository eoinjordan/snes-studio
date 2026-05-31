# Features

## Launch showcase game

SNES Studio opens on **Pocket Bugs**, an original garden-bug battler. You catch bugs in the backyard, carry them in small matchboxes, and battle in a local tournament across exploration and arena scenes. It's authored entirely with SNES Studio's own scene/sprite/event-chain model - regenerate it with `python scripts/make_pocket_bugs.py`.

## 1.0.0 included

- React editor with project, scene, asset, inspector, helper, and build-check panels.
- Browser online demo mode with fallback sample project.
- Local backend mode through FastAPI.
- Scene model with actors, collision rectangles, and trigger zones.
- Sprite model with palettes and pixel frames.
- Event-chain model with nested `if_flag` support.
- Block palette definitions for dialogue, actor, scene, logic, timing, and sound actions.
- Human-reviewed helper patch workflow.
- Safe editor operations for scenes, actors, collisions, triggers, sprites, and event chains.
- CLI for validation, inventory, patching, editor operations, C export, and build workflow testing.
- Generated C stubs from project data.
- Placeholder `.sfc` artifact generation for workflow testing.
- GitHub Actions for tests, frontend build, Pages deploy, and release artifact workflows.
- Native SNES asset conversion: pixel sprites -> 4bpp tiles + BGR555 palettes, scenes -> 32x32 background tilemaps.
- Generated PVSnesLib runtime engine (top-down overworld: walk + tilemap collision + dialogue boxes).
- Integrated EmulatorJS ROM Preview (load and play a homebrew `.sfc`/`.smc` in-browser).
- One-click deploy configs for Vercel (`vercel.json`) and Netlify (`netlify.toml`).

## Not included yet

- True Blockly drag/drop workspace.
- Multi-user classroom accounts.
- A hosted (cloud) ROM build service â€” building still requires local PVSnesLib.

