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


def bg_tileset() -> bytes:
    """Four flat 8x8 4bpp tiles (one per palette index 0..3)."""
    data = bytearray()
    for idx in range(4):
        data.extend(_tile_4bpp([idx] * (TILE_PX * TILE_PX)))
    return bytes(data)


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
    """Render (header, source) C for the bg tileset/palette and per-scene maps."""
    tiles = bg_tileset()
    pal = palette_to_cgram(BG_PALETTE)
    h = ["#ifndef SNESSTUDIO_MAPS_H", "#define SNESSTUDIO_MAPS_H", "",
         "/* Generated SNES background tilemaps (32x32) + built-in bg tileset. */",
         f"#define MAP_W {MAP_W}", f"#define MAP_H {MAP_H}",
         f"#define BG_TILESET_TILES {len(tiles) // BYTES_PER_TILE}",
         f"extern const unsigned char gfx_bgtiles[{len(tiles)}];",
         "extern const unsigned short pal_bg[16];", ""]
    c = ['#include "snesstudio_maps.h"', "",
         _c_byte_array("gfx_bgtiles", tiles), "",
         _c_word_array("pal_bg", pal), ""]
    for scene in project.scenes:
        ident = c_ident(scene.id)
        words = scene_tilemap(scene)
        h += [f"/* scene '{scene.id}' ({scene.name}) */",
              f"extern const unsigned short map_{ident}[{len(words)}];", ""]
        c += [_c_word_array(f"map_{ident}", words), ""]
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
