# SNES Studio 1.0.0

SNES Studio is a kid-friendly, human-in-the-loop, agent-assisted game builder for Super Nintendo homebrew projects.

![SNES Studio UI](web-ui-screenshot.png)

This 1.0.0 repository is a complete publishable MVP. It gives you a polished editor shell, a real project model, scene editing primitives, sprite editing primitives, event-chain logic, safe agent patch review, C export, GitHub Pages demo mode, and local backend mode.

The studio opens on its flagship template game, **Poachermon — "Gotta Save 'Em All!"** — a comedic savannah safari where a park ranger rescues wild creatures from a poacher across four scenes. It's built entirely from SNES Studio's own scene/sprite/event model (`python scripts/make_poachermon.py`).

It is intentionally honest about the current technical boundary: **the editor and compiler pipeline work, while real playable SNES ROM generation still requires finishing the PVSnesLib runtime integration.** The current `--skip-build` command produces a placeholder `.sfc` artifact for release workflow testing, not a playable game.

## Why this exists

Most beginner game tools either hide all code or expose too much code too early. SNES Studio uses a different workflow:

```text
Kid idea
  -> helper proposes a patch
  -> kid or mentor reviews it
  -> patch is applied safely
  -> project validates
  -> event chains compile to readable C stubs
  -> ROM build workflow is prepared
```

The agent never silently edits the game. Every helper change is reviewable.

## Main features

- Polished React editor UI
- GitHub Pages online demo mode
- Local Python/FastAPI backend mode
- Scene list and scene canvas
- Actor editing: add, update, delete, move
- Collision and trigger zones
- Pixel sprite editor data model
- Event chain editor data model
- Block palette definitions
- Human-reviewed agent patches
- Safe backup-before-write server behavior
- Project import/export as `.snesproj`
- Generated C export using Jinja templates
- CLI workflow for classrooms and CI
- GitHub Actions for backend tests, frontend build, Pages deploy, and release artifacts

## Quick start: backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,server]"

snes-studio validate examples/hello-human/project.snesproj
snes-studio inventory examples/hello-human/project.snesproj
snes-studio serve examples/hello-human/project.snesproj --host 127.0.0.1 --port 8765
```

## Quick start: frontend

```bash
cd web
npm install
npm run dev
```

Open the Vite URL. If the backend is running, the UI uses local builder mode. If not, it falls back to online demo mode and loads the bundled sample project.

## CLI examples

```bash
snes-studio validate examples/hello-human/project.snesproj --json
snes-studio inventory examples/hello-human/project.snesproj --json
snes-studio export-c examples/hello-human/project.snesproj build/generated/hello-human --json
snes-studio make:rom examples/hello-human/project.snesproj build/hello-human.sfc --skip-build --json
scripts/validate-rom.sh build/hello-human.sfc
```

## Editor API examples

```bash
snes-studio add-scene examples/hello-human/project.snesproj --id lab --name "Robot Lab"
snes-studio add-actor examples/hello-human/project.snesproj --scene lab --id mentor --name "Mentor Bot" --x 80 --y 120 --sprite robot
snes-studio add-event-chain examples/hello-human/project.snesproj --id mentor_intro --name "Mentor Intro"
snes-studio add-step examples/hello-human/project.snesproj --chain mentor_intro --type show_text --text "Welcome to SNES Studio."
```

## Building a real ROM: PVSnesLib toolchain setup

The asset/tilemap pipeline and the generated C are produced and tested **without**
any SNES toolchain. Only the final ROM assembly needs **PVSnesLib**. Once it is
installed, `make:rom` (without `--skip-build`) compiles a real `.sfc`.

The generated build directory contains everything needed: `main.c`, the
PVSnesLib engine `snesstudio_snes.c`, pre-converted `snesstudio_assets.c`
(4bpp tiles + BGR555 palettes), `snesstudio_maps.c` (background tilemaps), and a
`Makefile`.

### 1. Install PVSnesLib

```bash
# Linux/macOS (see https://github.com/alekmaul/pvsneslib for the latest)
git clone https://github.com/alekmaul/pvsneslib.git
cd pvsneslib
# Follow the repo's install instructions for your OS, then:
export PVSNESLIB_HOME=/absolute/path/to/pvsneslib
```

On Windows, use the PVSnesLib release installer or WSL, then set
`PVSNESLIB_HOME` to the install path.

### 2. Convert + build

```bash
snes-studio export-assets   examples/hello-human/project.snesproj build/generated/hello-human
snes-studio export-tilemaps examples/hello-human/project.snesproj build/generated/hello-human
snes-studio export-c        examples/hello-human/project.snesproj build/generated/hello-human
snes-studio make:rom        examples/hello-human/project.snesproj build/hello-human.sfc   # no --skip-build
```

`make:rom` shells out to `make` in the generated directory. If `PVSNESLIB_HOME`
is unset or the toolchain is missing, it fails with a clear message; use
`--skip-build` to produce a placeholder `.sfc` for workflow/CI testing instead.

### 3. Run it

Load `build/hello-human.sfc` in any SNES emulator (bsnes, Mesen-S, Snes9x). The
generated engine is a top-down overworld: the D-pad walks the player sprite with
tilemap collision, and `show_text` event steps render a dialogue box (advance
with **A**).

> PVSnesLib helper signatures vary slightly between versions. If a PPU/OAM call
> in `snesstudio_snes.c` does not match your installed headers, each call is
> commented with its intent so it is quick to adjust. See `docs/ENGINE.md`.

## ROM Preview (EmulatorJS)

The **ROM Preview** tab plays a homebrew SNES ROM in the browser using
[EmulatorJS](https://emulatorjs.org/). Click **Load .sfc / .smc**, pick a ROM you
built with `snes-studio make:rom` (or any homebrew ROM you own), and play it. No
copyrighted ROMs are bundled and files never leave your browser. See
`docs/EMULATOR.md`.

## Hosting the UI for free

The web UI is a static Vite app (online demo mode — no backend needed). Deploy
it on any static host:

- **Vercel** — import the repo; `vercel.json` builds `web/` and serves `web/dist`.
- **Netlify** — import the repo; `netlify.toml` sets base `web/`, publish `dist`.
- **GitHub Pages** — push to GitHub and enable Pages; `.github/workflows/pages.yml`
  builds and deploys `web/` automatically.

All three host only the editor + EmulatorJS front-end. They cannot run the Python
backend or build ROMs — that needs local mode or a future hosted build service.

A hosted static deploy can:

- load a bundled sample project
- edit scenes, actors, sprites, and event chains in the browser
- propose deterministic safe patches
- apply patches after human review
- download `.snesproj`
- play a homebrew `.sfc`/`.smc` you load in the ROM Preview tab

## What 1.0.0 means

Version 1.0.0 means the repository is clean, publishable, documented, testable, and suitable as a public open-source starting point. It does not mean feature parity with GB Studio or a production-ready SNES compiler.

## Roadmap

See:

- `docs/ROADMAP.md`
- `docs/FEATURES.md`
- `docs/ISSUES.md`
- `docs/TOOLCHAIN.md`
- `docs/EMULATOR.md`
- `docs/HUMAN_IN_THE_LOOP.md`
