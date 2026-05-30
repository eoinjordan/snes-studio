# Toolchain

Tests and the web demo need **no** SNES toolchain. Building a real, playable
`.sfc` needs **PVSnesLib** (which bundles its own 65816 C compiler `816-tcc`,
`wla-65816` assembler/linker, and `gfx4snes`). The placeholder path needs
nothing:

```bash
# placeholder artifact for CI / release-workflow testing (not playable)
snes-studio make:rom examples/poachermon/project.snesproj build/poachermon.sfc --skip-build
```

## Real ROM build (verified with PVSnesLib 4.5.0 on Windows)

1. **Install PVSnesLib** — download the release for your OS from
   <https://github.com/alekmaul/pvsneslib/releases> and unzip it, e.g. to
   `C:\pvsneslib-install\pvsneslib`. You also need `make` (devkitPro's MSYS2
   provides it on Windows; on Linux/macOS use your package manager).

2. **Set `PVSNESLIB_HOME` in Unix style** — even on Windows the path must use
   `/c/...`, not `C:\...`:

   ```powershell
   # Windows (persist for all future shells)
   [Environment]::SetEnvironmentVariable("PVSNESLIB_HOME", "/c/pvsneslib-install/pvsneslib", "User")
   ```
   ```bash
   # Linux / macOS
   export PVSNESLIB_HOME=/absolute/path/to/pvsneslib
   ```

3. **Build** (no `--skip-build`):

   ```bash
   snes-studio make:rom examples/poachermon/project.snesproj build/poachermon.sfc
   ```

   This exports the C + converted assets, then runs PVSnesLib's `make`. The
   result is a ~256 KB LoROM `.sfc` with a valid SNES header that boots in
   Snes9x / bsnes / Mesen-S and the in-app **ROM Preview** (EmulatorJS) tab.

### Notes / gotchas

* `PVSNESLIB_HOME` **must** be `/c/...` style or snes_rules aborts immediately.
* The generated engine targets the PVSnesLib 4.5.0 API (`OBJ_SIZE16_L32`,
  `oamInitGfxSet`, `bgInitTileSet/MapSet`). Generated C is C89 (816-tcc), so no
  C99 inline-`for` declarations.
* `snes_rules` compiles every `.c` in the build dir, so SNES Studio emits only
  the SNES engine there (the desktop printf stub is not exported). For
  toolchain-free logic testing, use `snes-studio play <project>`.
* Background tile/VRAM layout is still being refined — the ROM boots and runs;
  pixel-perfect scene rendering is an ongoing engine polish item.
