"""SNES asset conversion pipeline.

Converts SNES Studio sprite data (palette-indexed pixel frames + hex palettes)
into the binary formats the SNES PPU actually consumes:

* tiles  -> 4bpp planar, 32 bytes per 8x8 tile (PVSnesLib / standard SNES order)
* colors -> 15-bit BGR555 words for CGRAM

This is engine-foundation code (roadmap 1.2.0: "Convert pixel sprite data to
SNES tile assets"). It is pure and deterministic so it can be tested without a
SNES toolchain. The emitted C arrays are consumed by the generated runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import Project, Sprite
from .project import load_project
from .compiler import c_ident

TILE = 8                      # SNES tiles are 8x8 pixels
BYTES_PER_TILE = 32           # 4bpp -> 4 bitplanes * 8 rows = 32 bytes


def hex_to_bgr555(color: str) -> int:
    """Convert a CSS hex color (#rgb or #rrggbb) to a 15-bit BGR555 word."""
    s = (color or "#000000").lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"invalid hex color: {color!r}")
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)


def palette_to_cgram(palette: list[str], size: int = 16) -> list[int]:
    """Convert a hex palette to a fixed-size list of BGR555 words (zero padded)."""
    words = [hex_to_bgr555(c) for c in palette[:size]]
    words.extend([0] * (size - len(words)))
    return words


def _tile_4bpp(block: list[int]) -> bytes:
    """Encode one 8x8 block of palette indices (0..15) as 4bpp planar bytes.

    Layout: bitplanes 0&1 interleaved per row for the first 16 bytes, then
    bitplanes 2&3 for the last 16 bytes. Bit 7 of each byte is the leftmost pixel.
    """
    out = bytearray(BYTES_PER_TILE)
    for y in range(TILE):
        p0 = p1 = p2 = p3 = 0
        for x in range(TILE):
            px = block[y * TILE + x] & 0xF
            bit = 7 - x
            p0 |= ((px >> 0) & 1) << bit
            p1 |= ((px >> 1) & 1) << bit
            p2 |= ((px >> 2) & 1) << bit
            p3 |= ((px >> 3) & 1) << bit
        out[y * 2] = p0
        out[y * 2 + 1] = p1
        out[16 + y * 2] = p2
        out[16 + y * 2 + 1] = p3
    return bytes(out)


def frame_to_tiles(pixels: list[int], width: int, height: int) -> bytes:
    """Convert a full frame of palette indices into concatenated 4bpp tiles.

    Tiles are emitted in raster order of 8x8 blocks: left-to-right, top-to-bottom.
    Width/height are padded up to a multiple of 8 with transparent pixels (index 0).
    """
    pw = (width + TILE - 1) // TILE * TILE
    ph = (height + TILE - 1) // TILE * TILE
    # Re-pack into a padded grid so indexing is uniform.
    grid = [0] * (pw * ph)
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            grid[y * pw + x] = pixels[idx] if idx < len(pixels) else 0
    data = bytearray()
    for ty in range(0, ph, TILE):
        for tx in range(0, pw, TILE):
            block = [grid[(ty + by) * pw + (tx + bx)] for by in range(TILE) for bx in range(TILE)]
            data.extend(_tile_4bpp(block))
    return bytes(data)


def sprite_assets(sprite: Sprite | dict[str, Any]) -> dict[str, Any]:
    """Return the converted tile/palette data for one sprite."""
    s = sprite if isinstance(sprite, Sprite) else Sprite.model_validate(sprite)
    area = s.width * s.height
    frames = []
    for frame in s.frames:
        pixels = frame.pixels if len(frame.pixels) == area else [0] * area
        frames.append({"id": frame.id, "tiles": frame_to_tiles(pixels, s.width, s.height)})
    tiles_per_frame = ((s.width + TILE - 1) // TILE) * ((s.height + TILE - 1) // TILE)
    return {
        "id": s.id,
        "name": s.name,
        "width": s.width,
        "height": s.height,
        "tiles_per_frame": tiles_per_frame,
        "palette": palette_to_cgram(s.palette),
        "frames": frames,
    }


def _c_byte_array(name: str, data: bytes) -> str:
    rows = []
    for i in range(0, len(data), 16):
        rows.append("    " + ", ".join(f"0x{b:02x}" for b in data[i:i + 16]) + ",")
    body = "\n".join(rows) if rows else "    0x00,"
    return f"const unsigned char {name}[{len(data)}] = {{\n{body}\n}};"


def _c_word_array(name: str, words: list[int]) -> str:
    body = "    " + ", ".join(f"0x{w:04x}" for w in words)
    return f"const unsigned short {name}[{len(words)}] = {{\n{body}\n}};"


def render_assets(project: Project) -> tuple[str, str]:
    """Render (header, source) C strings for all sprites in the project."""
    sprites = [sprite_assets(s) for s in project.sprites]
    h = ["#ifndef SNESSTUDIO_ASSETS_H", "#define SNESSTUDIO_ASSETS_H", "",
         "/* Generated SNES assets: 4bpp tiles + BGR555 palettes. */", ""]
    c = ['#include "snesstudio_assets.h"', ""]
    for sp in sprites:
        ident = c_ident(sp["id"])
        all_tiles = b"".join(f["tiles"] for f in sp["frames"])
        total_tiles = len(all_tiles) // BYTES_PER_TILE
        h += [
            f"/* sprite '{sp['id']}' ({sp['name']}) {sp['width']}x{sp['height']}, "
            f"{len(sp['frames'])} frame(s), {sp['tiles_per_frame']} tile(s)/frame */",
            f"#define GFX_{ident.upper()}_W {sp['width']}",
            f"#define GFX_{ident.upper()}_H {sp['height']}",
            f"#define GFX_{ident.upper()}_TILES {total_tiles}",
            f"#define GFX_{ident.upper()}_TILES_PER_FRAME {sp['tiles_per_frame']}",
            f"extern const unsigned char gfx_{ident}_tiles[{len(all_tiles)}];",
            f"extern const unsigned short pal_{ident}[16];",
            "",
        ]
        c += [_c_byte_array(f"gfx_{ident}_tiles", all_tiles), "",
              _c_word_array(f"pal_{ident}", sp["palette"]), ""]
    h += ["#endif", ""]
    return "\n".join(h), "\n".join(c)


def export_assets(project_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    project = load_project(project_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    header, source = render_assets(project)
    (out / "snesstudio_assets.h").write_text(header, encoding="utf-8")
    (out / "snesstudio_assets.c").write_text(source, encoding="utf-8")
    return {
        "out_dir": str(out),
        "files": [str(out / "snesstudio_assets.h"), str(out / "snesstudio_assets.c")],
        "sprites": [s.id for s in project.sprites],
    }


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def sprite_from_image(
    sprite_id: str,
    name: str,
    image_path: str | Path,
    width: int = 16,
    height: int = 16,
    colors: int = 8,
) -> Sprite:
    """Create a SNES Studio Sprite by quantizing an input image.

    This is used by scripts/CLI to bootstrap art from real reference images.
    """
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError("Pillow is required for sprite import. Install with: pip install pillow") from exc

    colors = max(2, min(16, int(colors)))
    src = Image.open(Path(image_path)).convert("RGB")
    resized = src.resize((width, height), Image.Resampling.LANCZOS)
    paletted = resized.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
    pixels = list(paletted.getdata())
    raw = paletted.getpalette() or []
    palette: list[str] = []
    for i in range(colors):
        base = i * 3
        if base + 2 >= len(raw):
            break
        palette.append(_rgb_to_hex((raw[base], raw[base + 1], raw[base + 2])))
    if not palette:
        palette = ["#000000", "#ffffff"]
    return Sprite.model_validate({
        "id": sprite_id,
        "name": name,
        "width": width,
        "height": height,
        "palette": palette,
        "frames": [{"id": f"{sprite_id}_0", "name": "Frame 0", "pixels": pixels}],
    })
