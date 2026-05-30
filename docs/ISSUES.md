# Current Issues

## Known technical boundaries

1. The generated `.sfc` from `--skip-build` is a placeholder artifact, not a playable SNES ROM.
2. The generated C is readable and testable as a compiler boundary, but not yet wired to a complete PVSnesLib runtime.
3. As of 1.1.0 the web UI performs real mutations (create/update/delete, drag-move, pixel painting, click-to-add steps) in both backend and online demo mode. Collision/trigger drawing tools remain UI-first.
4. GitHub Pages cannot run the Python backend or build ROMs.
5. EmulatorJS is documented but not bundled in 1.0.0 to avoid license and asset confusion.

## High-priority next issues

- [x] Implement real actor drag/move writes.
- [x] Implement sprite pixel painting writes.
- [x] Add UI forms for scene/actor/event creation.
- Add collision/trigger zone drawing (currently render-only).
- Add PVSnesLib runtime text box.
- Add tile conversion pipeline.
- Add browser ROM preview without bundling copyrighted ROMs.
