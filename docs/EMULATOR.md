# Emulator Preview

**Integrated.** The web UI's **ROM Preview** tab embeds
[EmulatorJS](https://emulatorjs.org/) (SNES core) loaded from its public CDN
(`https://cdn.emulatorjs.org/stable/data/`). Click **Load .sfc / .smc** (or the
**Preview ROM** button in the top bar) to pick a homebrew ROM and play it in the
browser.

Implementation: `RomPreview` in [`web/src/main.jsx`](../web/src/main.jsx). The
selected file becomes an object URL handed to EmulatorJS via its `EJS_*` window
globals; each ROM load remounts a fresh host element (React `key`) so a new game
starts cleanly.

Rules honored:

- No copyrighted ROMs are bundled — the user loads their own `.sfc`/`.smc`.
- Files never leave the browser (object URLs, no upload).
- EmulatorJS is loaded from its CDN, not vendored, so its license stays at arm's
  length. If you later vendor it, review its licensing.
- ROM *building* stays separate from static hosting (see below).

Product flow:

```text
Edit project -> build .sfc locally (PVSnesLib) -> load it in ROM Preview -> play
```

The static GitHub Pages / Vercel / Netlify deploy hosts only the editor + the
emulator front-end. It cannot build ROMs; that needs local mode (`snes-studio
make:rom`) or a future hosted build service.
