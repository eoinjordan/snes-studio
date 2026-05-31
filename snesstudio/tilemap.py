"""SNES background tilemap conversion.

Derives a playable background tilemap for each scene and emits it in the SNES
PPU tilemap format (32x32 grid of 16-bit entries) plus a small built-in
background tileset and palette.

Source data: scenes do not yet carry hand-painted tile grids, so we synthesize
a top-down adventure map deterministically from existing scene structure:

* the whole map is floor,
* the outer border is wall,
* every collision rect becomes solid wall tiles.

This gives the overworld runtime a real, walkable map + collision shape today,
and is the seam where a future tilemap-painting UI plugs in. Pure & testable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import Project, Scene
from .project import load_project
from .compiler import c_ident
from .assets import _tile_4bpp, palette_to_cgram, BYTES_PER_TILE

TILE_PX = 8
MAP_W = 32                      # SC_32x32 -> one 256x256 screen
MAP_H = 32

# Tile-based background grid: 16x14 metatiles of 16x16px = 256x224 (native res).
TILE_COLS, TILE_ROWS = 16, 14
FLAT_TILE_COUNT = 16            # flat colour tiles occupy bank indices 0..15
ASSET_DIR = Path(__file__).resolve().parent / "assets"


def load_bg_tileset(name: str = "overworld") -> dict:
    return json.loads((ASSET_DIR / f"bg_{name}.json").read_text(encoding="utf-8"))


def _metatile_subtiles(pixels: list[int]) -> list[list[int]]:
    """Split a 16x16 metatile into four 8x8 blocks in SNES order TL, TR, BL, BR."""
    subs = []
    for sy in (0, 1):
        for sx in (0, 1):
            subs.append([pixels[(sy * 8 + y) * 16 + (sx * 8 + x)] for y in range(8) for x in range(8)])
    return subs


def build_real_bank(tileset: dict, base_index: int = FLAT_TILE_COUNT) -> tuple[list[list[int]], list[list[int]]]:
    """Return (unique 8x8 blocks, per-metatile [TL,TR,BL,BR] bank indices)."""
    bank: list[list[int]] = []
    seen: dict[tuple[int, ...], int] = {}
    meta_map: list[list[int]] = []
    for mt in tileset["tiles"]:
        idxs = []
        for block in _metatile_subtiles(mt["pixels"]):
            key = tuple(block)
            if key not in seen:
                seen[key] = base_index + len(bank)
                bank.append(block)
            idxs.append(seen[key])
        meta_map.append(idxs)
    return bank, meta_map


def scene_is_tiled(scene: Scene) -> bool:
    return bool(getattr(scene, "tilemap", None))


def tiled_map_and_collision(scene: Scene, tileset: dict, meta_map: list[list[int]]) -> tuple[list[int], list[int]]:
    """Build a 32x32 SNES tilemap + collision grid from a scene's 16x14 metatiles."""
    grid = [tile_entry(0)] * (MAP_W * MAP_H)
    col = [0] * (MAP_W * MAP_H)
    tm = scene.tilemap or []
    solids = [bool(t.get("solid")) for t in tileset["tiles"]]
    for r in range(TILE_ROWS):
        for c in range(TILE_COLS):
            mi = tm[r * TILE_COLS + c] if r * TILE_COLS + c < len(tm) else 0
            if mi < 0 or mi >= len(meta_map):
                mi = 0
            tl, tr, bl, br = meta_map[mi]
            bx, by = 2 * c, 2 * r
            grid[by * MAP_W + bx] = tile_entry(tl)
            grid[by * MAP_W + bx + 1] = tile_entry(tr)
            grid[(by + 1) * MAP_W + bx] = tile_entry(bl)
            grid[(by + 1) * MAP_W + bx + 1] = tile_entry(br)
            if solids[mi]:
                for dy in (0, 1):
                    for dx in (0, 1):
                        col[(by + dy) * MAP_W + (bx + dx)] = 1
    return grid, col

# Background tile chars (indices into the built-in bg tileset / bg palette).
BG_FLOOR = 1
BG_WALL = 3
BG_PALETTE = ["#1e293b", "#4ade80", "#a3e635", "#475569"]   # sky, floor, accent, wall


def tile_entry(tile: int, palette: int = 0, priority: bool = False,
               hflip: bool = False, vflip: bool = False) -> int:
    """Encode a SNES tilemap entry word (vhopppcc cccccccc)."""
    return ((tile & 0x3FF)
            | ((palette & 0x7) << 10)
            | ((1 if priority else 0) << 13)
            | ((1 if hflip else 0) << 14)
            | ((1 if vflip else 0) << 15))


def scene_tilemap(scene: Scene, w: int = MAP_W, h: int = MAP_H) -> list[int]:
    """Build a w*h tilemap (row-major) for a scene from its collision rects."""
    floor = tile_entry(BG_FLOOR)
    wall = tile_entry(BG_WALL)
    grid = [floor] * (w * h)
    for y in range(h):
        for x in range(w):
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                grid[y * w + x] = wall
    for rect in scene.collision:
        tx0, ty0 = rect.x // TILE_PX, rect.y // TILE_PX
        tx1 = (rect.x + rect.w - 1) // TILE_PX
        ty1 = (rect.y + rect.h - 1) // TILE_PX
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if 0 <= tx < w and 0 <= ty < h:
                    grid[ty * w + tx] = wall
    return grid


PAINT_COLS, PAINT_ROWS = 32, 28      # editor paint grid (matches web SCENE_COLS/ROWS)
VISIBLE_ROWS = 28                    # 28*8 = 224px screen height


def bg_tileset() -> bytes:
    """Sixteen flat 8x8 4bpp tiles, one solid tile per palette index 0..15.

    The painted background just indexes these by colour, so a scene's look is
    entirely defined by its per-scene palette."""
    data = bytearray()
    for idx in range(16):
        data.extend(_tile_4bpp([idx] * (TILE_PX * TILE_PX)))
    return bytes(data)


def _sanitize_palette(colors: list[str]) -> list[str]:
    """Editor palettes may carry 'transparent' (index 0); map non-hex to black."""
    return [c if isinstance(c, str) and c.startswith("#") else "#000000" for c in colors]


def scene_is_painted(scene: Scene) -> bool:
    return bool(scene.paint_palette) and any(v for v in (scene.paint or []))


def painted_tilemap(scene: Scene) -> list[int]:
    """32x32 map from the editor's 32x28 paint grid (off-screen rows = 0)."""
    grid = [tile_entry(0)] * (MAP_W * MAP_H)
    paint = scene.paint or []
    for r in range(min(PAINT_ROWS, MAP_H)):
        for c in range(min(PAINT_COLS, MAP_W)):
            idx = paint[r * PAINT_COLS + c] if r * PAINT_COLS + c < len(paint) else 0
            grid[r * MAP_W + c] = tile_entry(idx & 0xF)
    return grid


def scene_collision_grid(scene: Scene) -> list[int]:
    """32x32 byte grid (1 = solid) from the scene's collision rectangles."""
    grid = [0] * (MAP_W * MAP_H)
    for rect in scene.collision:
        tx0, ty0 = rect.x // TILE_PX, rect.y // TILE_PX
        tx1 = (rect.x + rect.w - 1) // TILE_PX
        ty1 = (rect.y + rect.h - 1) // TILE_PX
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
                    grid[ty * MAP_W + tx] = 1
    return grid


def scene_palette(scene: Scene) -> list[int]:
    colors = _sanitize_palette(scene.paint_palette) if scene.paint_palette else BG_PALETTE
    return palette_to_cgram(colors, 16)


def _c_word_array(name: str, words: list[int]) -> str:
    rows = []
    for i in range(0, len(words), 16):
        rows.append("    " + ", ".join(f"0x{w:04x}" for w in words[i:i + 16]) + ",")
    body = "\n".join(rows) if rows else "    0x0000,"
    return f"const unsigned short {name}[{len(words)}] = {{\n{body}\n}};"


def _c_byte_array(name: str, data: bytes) -> str:
    rows = []
    for i in range(0, len(data), 16):
        rows.append("    " + ", ".join(f"0x{b:02x}" for b in data[i:i + 16]) + ",")
    body = "\n".join(rows) if rows else "    0x00,"
    return f"const unsigned char {name}[{len(data)}] = {{\n{body}\n}};"


def render_tilemaps(project: Project) -> tuple[str, str]:
    """Render (header, source) C: bg tileset + per-scene map, collision, palette.

    The tile bank is [16 flat colour tiles][real 8x8 tiles from the bundled
    tileset]. Tile-painted scenes use the real tiles and the shared overworld
    palette; legacy painted scenes keep the flat tiles + their per-scene palette;
    everything else falls back to a synthesized floor/wall map.
    """
    tileset = load_bg_tileset("overworld")
    real_bank, meta_map = build_real_bank(tileset, base_index=FLAT_TILE_COUNT)
    tiles = bg_tileset() + b"".join(_tile_4bpp(b) for b in real_bank)
    bg_overworld_pal = palette_to_cgram(tileset["palette"], 16)
    wall = tile_entry(BG_WALL)
    h = ["#ifndef SNESSTUDIO_MAPS_H", "#define SNESSTUDIO_MAPS_H", "",
         "/* Generated SNES backgrounds: flat colour tiles + a real overworld",
         "   tileset, then per-scene tilemap, collision grid and palette. */",
         f"#define MAP_W {MAP_W}", f"#define MAP_H {MAP_H}",
         f"#define VISIBLE_ROWS {VISIBLE_ROWS}",
         f"#define BG_TILESET_TILES {len(tiles) // BYTES_PER_TILE}",
         f"extern const unsigned char gfx_bgtiles[{len(tiles)}];",
         "extern const unsigned short pal_bg[16];", ""]
    c = ['#include "snesstudio_maps.h"', "",
         _c_byte_array("gfx_bgtiles", tiles), "",
         _c_word_array("pal_bg", palette_to_cgram(BG_PALETTE, 16)), ""]
    for scene in project.scenes:
        ident = c_ident(scene.id)
        tiled = scene_is_tiled(scene)
        painted = (not tiled) and scene_is_painted(scene)
        if tiled:
            words, col = tiled_map_and_collision(scene, tileset, meta_map)
            for i, v in enumerate(scene_collision_grid(scene)):
                if v:
                    col[i] = 1
            pal = bg_overworld_pal
            tag = " [tiled]"
        else:
            words = painted_tilemap(scene) if painted else scene_tilemap(scene)
            col = scene_collision_grid(scene)
            if not painted:
                for i, w in enumerate(words):
                    if w == wall:
                        col[i] = 1
            pal = scene_palette(scene)
            tag = " [painted]" if painted else ""
        h += [f"/* scene '{scene.id}' ({scene.name}){tag} */",
              f"extern const unsigned short map_{ident}[{len(words)}];",
              f"extern const unsigned char col_{ident}[{len(col)}];",
              f"extern const unsigned short pal_{ident}[16];", ""]
        c += [_c_word_array(f"map_{ident}", words), "",
              _c_byte_array(f"col_{ident}", bytes(col)), "",
              _c_word_array(f"pal_{ident}", pal), ""]
    h += ["#endif", ""]
    return "\n".join(h), "\n".join(c)


def export_tilemaps(project_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    project = load_project(project_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    header, source = render_tilemaps(project)
    (out / "snesstudio_maps.h").write_text(header, encoding="utf-8")
    (out / "snesstudio_maps.c").write_text(source, encoding="utf-8")
    return {
        "out_dir": str(out),
        "files": [str(out / "snesstudio_maps.h"), str(out / "snesstudio_maps.c")],
        "scenes": [s.id for s in project.scenes],
    }
