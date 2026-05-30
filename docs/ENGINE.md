# Engine Foundation & Adventure/RPG Vertical

This document tracks the playable-runtime engine work (roadmap 1.2.0–1.3.0) and
the plan for the first genre vertical: **adventure / top-down RPG** (the
Monkey Island → Pokémon/Final Fantasy IV family).

We are building **one vertical end-to-end to a playable `.sfc`** before
generalising. Fighting games (Street Fighter) and pseudo-3D racers (Road Rash)
are deliberately out of scope for this phase — they need fundamentally different
engines and share little with the current scene/actor/dialogue model.

## Why this vertical first

The existing data model already maps onto adventure/RPG concepts:

| Model concept | Adventure/RPG use |
|---|---|
| Scene + background | Map / room |
| Actor + sprite | Player, NPCs, objects |
| Event chain + trigger | Dialogue, cutscenes, scripted logic |
| Flags / variables | Quest state, story progress, stats |
| Collision / trigger zones | Walls, doors, scene transitions |

## Engine layers (build order)

1. **Asset pipeline** — convert editor data to PPU formats. ✅ *started*
   - `snesstudio/assets.py`: sprite pixel frames → 4bpp planar tiles;
     hex palettes → BGR555 CGRAM words. Emitted as C arrays
     (`snesstudio_assets.h/.c`), wired into `export-c` and `export-assets`.
   - Next: background tilemaps, shared tilesets, font/text tiles.
2. **PVSnesLib runtime** — replace the desktop `printf` stub runtime with real
   PPU/OAM/VRAM calls. Bring up: init video, load a palette + tiles, show one
   sprite, read the controller.
3. **Overworld loop** — player sprite moving on a tilemap, D-pad input, AABB
   collision against collision rects, facing direction → sprite frame.
4. **Dialogue / text box** — windowed text rendering driven by the existing
   `show_text` event step; advance on A. This is the first thing that makes the
   adventure genre feel real.
5. **Scene transitions** — `change_scene` event + trigger zones load a new map.
6. **RPG systems** (Pokémon/FF4 depth) — turn-based battle scene, party + stats
   data tables, menu rendering, encounters. Layered on top of 4–5.

## Toolchain reality

A real ROM build requires **PVSnesLib** (816-tcc, wla-dx, the `816` toolchain)
installed locally — see `docs/TOOLCHAIN.md`. `make:rom --skip-build` still emits
a placeholder `.sfc` for workflow/CI testing. The asset pipeline and generated C
are produced and tested **without** the toolchain; only the final assembly step
needs it. `make:rom` (no `--skip-build`) shells out to `make` in the generated
build dir and fails with a clear message if the toolchain is absent.

## Status

- [x] 1.2.0 — Convert pixel sprite data to SNES tile assets (`assets.py`).
- [ ] 1.2.0 — Background tilemap conversion.
- [ ] 1.2.0 — PVSnesLib runtime: video init + sprite + controller.
- [ ] 1.2.0 — Overworld movement + collision loop.
- [ ] 1.2.0 — Text box rendering from `show_text`.
- [ ] 1.3.0 — EmulatorJS browser preview of built `.sfc` (no bundled ROMs).
- [ ] 2.x — Turn-based battle + party/stats for RPG depth.
