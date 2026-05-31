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

from pathlib import Path
from typing import Any

from .schema import Project, Scene
from .project import load_project
from .compiler import c_ident
from .assets import _tile_4bpp, palette_to_cgram, BYTES_PER_TILE

TILE_PX = 8
MAP_W = 32                      # SC_32x32 -> one 256x256 screen
MAP_H = 32

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
    """Render (header, source) C: bg tileset + per-scene map, collision, palette."""
    tiles = bg_tileset()
    wall = tile_entry(BG_WALL)
    h = ["#ifndef SNESSTUDIO_MAPS_H", "#define SNESSTUDIO_MAPS_H", "",
         "/* Generated SNES backgrounds: 16 flat bg tiles + per-scene tilemap,",
         "   collision grid and palette. Painted scenes use the editor paint grid;",
         "   others fall back to a synthesized floor/wall map. */",
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
        painted = scene_is_painted(scene)
        words = painted_tilemap(scene) if painted else scene_tilemap(scene)
        col = scene_collision_grid(scene)
        if not painted:
            for i, w in enumerate(words):
                if w == wall:
                    col[i] = 1
        pal = scene_palette(scene)
        h += [f"/* scene '{scene.id}' ({scene.name}){' [painted]' if painted else ''} */",
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
