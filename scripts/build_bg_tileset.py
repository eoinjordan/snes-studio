"""Build the bundled overworld background tileset for SNES Studio.

Slices a curated set of 16x16 overworld metatiles from the bundled OpenGameArt
Tuxemon tileset (Buch, CC-BY-SA 3.0) and adds a couple of procedurally-drawn
tiles (water, plain floor) for terrain the source sheet lacks. Everything is
quantized to ONE shared 16-color SNES BG palette (index 0 reserved as the
backdrop), so the whole set fits a single SNES background palette.

Outputs an identical JSON tileset to:
  - snesstudio/assets/bg_overworld.json   (used by the C exporter)
  - web/public/assets/bg_overworld.json   (used by the editor canvas)
plus a preview PNG for eyeballing.

JSON shape:
  {"name", "tile_px":16, "palette":[16 "#rrggbb"],
   "tiles":[{"id","name","solid":bool,"pixels":[256 ints 0..15]}]}
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TUX = ROOT / "build" / "assetpacks" / "listed" / "tuxemon-sheet.png"
TS = 16

# Clean grass tile; every other Tuxemon slice is composited over it so the
# sheet's transparent object pixels become grass instead of white.
GRASS = (5, 5)

# (name, col, row, solid). Coordinates are the 16px Tuxemon grid.
SLICES = [
    ("grass", 5, 5, False),
    ("sand", 5, 7, False),
    ("flowers", 0, 5, False),
    ("bush", 1, 5, False),
    ("tree", 1, 3, True),
    ("log", 0, 6, True),
    ("rock", 5, 2, True),
    ("fence_wood", 0, 9, True),
    ("fence_stone", 3, 9, True),
]


def crop_tux(col: int, row: int) -> Image.Image:
    sheet = Image.open(TUX).convert("RGBA")
    grass = sheet.crop((GRASS[0] * TS, GRASS[1] * TS, GRASS[0] * TS + TS, GRASS[1] * TS + TS))
    tile = sheet.crop((col * TS, row * TS, col * TS + TS, row * TS + TS))
    base = grass.copy()
    base.alpha_composite(tile)
    return base.convert("RGB")


def water_tile() -> Image.Image:
    img = Image.new("RGB", (TS, TS), (48, 104, 176))
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            # gentle ripple banding
            if (x + (y // 2)) % 6 == 0:
                px[x, y] = (96, 156, 208)
            elif (x + y) % 7 == 0:
                px[x, y] = (32, 80, 144)
    return img


def floor_tile() -> Image.Image:
    img = Image.new("RGB", (TS, TS), (196, 170, 124))
    px = img.load()
    for y in range(TS):
        for x in range(TS):
            if (x * 3 + y * 5) % 11 == 0:
                px[x, y] = (172, 146, 100)
    return img


def build() -> dict:
    raw = []  # (name, solid, RGB image)
    for name, col, row, solid in SLICES:
        raw.append((name, solid, crop_tux(col, row)))
    raw.append(("water", True, water_tile()))
    raw.append(("floor", False, floor_tile()))

    # Shared palette: gather all colors, quantize to 15 (+ index 0 = backdrop black).
    allpx = []
    for _, _, img in raw:
        allpx.extend(img.getdata())
    counts = Counter(allpx)
    if len(counts) <= 15:
        pal_rgb = [c for c, _ in counts.most_common(15)]
    else:
        merged = Image.new("RGB", (len(raw) * TS, TS))
        for i, (_, _, img) in enumerate(raw):
            merged.paste(img, (i * TS, 0))
        q = merged.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        rawpal = q.getpalette() or []
        pal_rgb = [(rawpal[i * 3], rawpal[i * 3 + 1], rawpal[i * 3 + 2]) for i in range(15)]
    palette = ["#000000"] + [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in pal_rgb]

    def nearest(rgb):
        best, bd = 1, 1 << 30
        for i, (r, g, b) in enumerate(pal_rgb):
            d = (rgb[0] - r) ** 2 + (rgb[1] - g) ** 2 + (rgb[2] - b) ** 2
            if d < bd:
                bd, best = d, i + 1  # +1: palette index 0 is the backdrop
        return best

    tiles = [{"id": "empty", "name": "Erase / empty", "solid": False, "pixels": [0] * (TS * TS)}]
    for name, solid, img in raw:
        pixels = [nearest(p) for p in img.getdata()]
        tiles.append({"id": name, "name": name.replace("_", " ").title(), "solid": solid, "pixels": pixels})

    return {"name": "Overworld (Tuxemon, CC-BY-SA + CC0 water/floor)", "tile_px": TS, "palette": palette, "tiles": tiles}


def save_preview(data: dict, out: Path, scale: int = 4) -> None:
    pal = [tuple(int(data["palette"][i].lstrip("#")[k:k + 2], 16) for k in (0, 2, 4)) for i in range(16)]
    n = len(data["tiles"])
    sheet = Image.new("RGB", (n * (TS + 2) * scale, (TS + 8) * scale), (30, 30, 30))
    for i, t in enumerate(data["tiles"]):
        img = Image.new("RGB", (TS, TS))
        for j, p in enumerate(t["pixels"]):
            img.putpixel((j % TS, j // TS), pal[p])
        sheet.paste(img.resize((TS * scale, TS * scale), Image.NEAREST), (i * (TS + 2) * scale, 2 * scale))
    sheet.save(out)


def main() -> None:
    data = build()
    for dest in [ROOT / "snesstudio" / "assets" / "bg_overworld.json",
                 ROOT / "web" / "public" / "assets" / "bg_overworld.json"]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data) + "\n", encoding="utf-8")
        print("wrote", dest.relative_to(ROOT))
    save_preview(data, ROOT / "tmp_bg_tileset_preview.png")
    print("tiles:", [t["id"] for t in data["tiles"]], "palette:", data["palette"])


if __name__ == "__main__":
    main()
