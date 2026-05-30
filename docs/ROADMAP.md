# Roadmap

## 1.0.0: Publishable MVP

Goal: clean public repo with a polished editor shell and safe human-in-the-loop workflow.

Delivered:

- Editor UI
- Online demo mode
- Local backend mode
- Project schema
- Scene, actor, sprite, collision, trigger, and event-chain data model
- Agent patch review
- Generated C stubs
- Placeholder ROM artifact flow

## 1.1.0: Real browser editing depth

- [x] Add real create/update/delete controls in the UI (scene/actor/event forms, actor delete, step delete).
- [x] Persist all editor operations through backend API or browser state (StudioClient editing methods for both modes).
- [x] Add drag-to-move actor support (pointer-drag on the scene canvas).
- [x] Add click-to-add event steps (block palette adds steps to the active chain).
- [x] Add sprite pixel painting writes (paintable grid backed by new `/api/sprites` route).
- [x] Open/import a `.snesproj` file into the browser editor.

## 1.2.0: Playable runtime

Target genre vertical: **adventure / top-down RPG** (Monkey Island → Pokémon/FF4).
See `docs/ENGINE.md` for the layered build plan.

- [x] Convert pixel sprite data to SNES tile assets (`snesstudio/assets.py`: 4bpp tiles + BGR555 palettes, `export-assets` CLI).
- [ ] Convert background data to SNES tilemaps.
- [ ] Replace C stubs with PVSnesLib runtime calls (video init, sprite, controller).
- [ ] Add actor movement and collision loop.
- [ ] Add basic text box rendering (from `show_text`).
- [ ] Build a real playable `.sfc`.

## 1.3.0: Emulator preview

- Integrate EmulatorJS.
- Allow loading homebrew `.sfc` files in browser.
- Feed locally built ROM blobs into preview panel.

## 2.0.0: Classroom product

- Project templates.
- Lesson mode.
- Mentor dashboard.
- Agent skill cards.
- Exportable worksheets.
