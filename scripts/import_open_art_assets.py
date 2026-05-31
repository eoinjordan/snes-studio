"""Import CC0 OpenGameArt sprite packs into bundled projects/templates.

Sources used by this script:
- Puny Characters by Shade, CC0: https://opengameart.org/content/puny-characters
- 16x16 Puny World Tileset by Shade, CC0: https://opengameart.org/content/16x16-puny-world-tileset
- 16x16 Puny Dungeon Tileset by Shade, CC0: https://opengameart.org/content/16x16-puny-dungeon-tileset
- Ambient Pixel Art Insects by madameberry, CC0: https://opengameart.org/content/ambient-pixel-art-insects

The source packs are downloaded into build/assetpacks and converted into the
palette-indexed JSON format used by .snesproj files. The projects therefore do
not depend on the downloaded files at runtime.
"""
from __future__ import annotations

import json
import shutil
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / "assetpacks"
COLS, ROWS = 32, 28

SOURCES = {
    "puny_characters": {
        "url": "https://opengameart.org/sites/default/files/puny-characters.zip",
        "file": CACHE / "puny-characters.zip",
        "dir": CACHE / "puny-characters",
    },
    "puny_world": {
        "url": "https://opengameart.org/sites/default/files/punyworld-overworld-tileset_0.png",
        "file": CACHE / "punyworld-overworld-tileset.png",
    },
    "puny_dungeon": {
        "url": "https://opengameart.org/sites/default/files/punyworld-dungeon-tileset.png",
        "file": CACHE / "punyworld-dungeon-tileset.png",
    },
    "cute_bugs": {
        "url": "https://opengameart.org/sites/default/files/cutebugs_by_madameberry.zip",
        "file": CACHE / "cutebugs_by_madameberry.zip",
        "dir": CACHE / "cutebugs",
    },
}

PROJECTS = [
    ROOT / "examples" / "hello-human" / "project.snesproj",
    ROOT / "web" / "public" / "examples" / "hello-human.snesproj",
    ROOT / "examples" / "mango-island" / "project.snesproj",
    ROOT / "web" / "public" / "examples" / "mango-island.snesproj",
    ROOT / "examples" / "poachermon" / "project.snesproj",
    ROOT / "web" / "public" / "examples" / "poachermon.snesproj",
    ROOT / "examples" / "pocket-bugs" / "project.snesproj",
    ROOT / "web" / "public" / "examples" / "pocket-bugs.snesproj",
    ROOT / "web" / "public" / "templates" / "dungeon-escape.snesproj",
    ROOT / "web" / "public" / "templates" / "town-tales.snesproj",
]

CHAR_DIR = CACHE / "puny-characters" / "Puny-Characters"
BUG_DIR = CACHE / "cutebugs"

CHARACTER_SHEETS = {
    "hero": "Warrior-Blue.png",
    "rival": "Warrior-Red.png",
    "judge": "Mage-Cyan.png",
    "ranger": "Archer-Green.png",
    "poacher": "Soldier-Red.png",
    "robot": "Soldier-Yellow.png",
    "npc": "Character-Base.png",
}

BUG_SHEETS = {
    "lady": "beetle.png",
    "beetle": "beetle.png",
    "mantis": "dragonfly.png",
    "moth": "moth.png",
    "bee": "bee.png",
    "slime": "Slime.png",
    "animal": "Slime.png",
}

# Hand-picked source rectangles from Puny World/Puny Dungeon sheets.
OBJECT_RECTS = {
    "tree": (0, 432, 32, 48),
    "house": (192, 480, 48, 48),
    "roof": (0, 656, 48, 32),
    "box": (112, 464, 32, 32),
    "sign": (64, 480, 32, 32),
    "chest": (80, 464, 32, 32),
    "stone": (0, 160, 32, 32),
}

SCENE_PALETTE = [
    "#050505", "#5fae4b", "#9ccc5a", "#c8a85a", "#1a9fb0", "#2f6b35",
    "#8a5a2b", "#d6b35d", "#d6d0a6", "#f7f1c2", "#d84a32", "#27313a",
    "#686f6a", "#aab0a2", "#e8874f", "#ffffff",
]


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response, path.open("wb") as out:
        shutil.copyfileobj(response, out)


def ensure_sources() -> None:
    for source in SOURCES.values():
        download(source["url"], source["file"])
        if "dir" in source and not source["dir"].exists():
            with zipfile.ZipFile(source["file"]) as zf:
                zf.extractall(source["dir"])


def rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def transparent_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = img.getchannel("A")
    return alpha.getbbox()


def fit_to_32(img: Image.Image, margin: int = 1) -> Image.Image:
    img = img.convert("RGBA")
    box = transparent_bbox(img)
    if not box:
        return Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    crop = img.crop(box)
    max_side = 32 - margin * 2
    scale = min(max_side / crop.width, max_side / crop.height)
    scale = max(1, int(scale)) if crop.width <= 16 and crop.height <= 16 else scale
    nw = max(1, min(max_side, int(crop.width * scale)))
    nh = max(1, min(max_side, int(crop.height * scale)))
    resized = crop.resize((nw, nh), Image.Resampling.NEAREST)
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    out.alpha_composite(resized, ((32 - nw) // 2, 32 - nh - 1))
    return out


def crop_character(sheet: str, col: int = 0, row: int = 0) -> Image.Image:
    src = rgba(CHAR_DIR / sheet)
    return fit_to_32(src.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)))


def crop_bug(sheet: str) -> Image.Image:
    if sheet == "Slime.png":
        src = rgba(CHAR_DIR / sheet).crop((0, 0, 32, 32))
    else:
        src = rgba(BUG_DIR / sheet)
    return fit_to_32(src, margin=2)


def crop_object(kind: str) -> Image.Image:
    if kind in {"stone", "chest"}:
        src = rgba(SOURCES["puny_dungeon"]["file"])
    else:
        src = rgba(SOURCES["puny_world"]["file"])
    x, y, w, h = OBJECT_RECTS.get(kind, OBJECT_RECTS["box"])
    return fit_to_32(src.crop((x, y, x + w, y + h)), margin=0)


def hex_color(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def quantized_palette(img: Image.Image, max_colors: int = 15) -> list[tuple[int, int, int]]:
    pixels = [(r, g, b) for r, g, b, a in img.getdata() if a >= 32]
    if not pixels:
        return [(255, 255, 255)]
    counts = Counter(pixels)
    if len(counts) <= max_colors:
        return [rgb for rgb, _ in counts.most_common(max_colors)]
    opaque = Image.new("RGB", img.size, (0, 0, 0))
    mask = img.getchannel("A")
    opaque.paste(img.convert("RGB"), mask=mask)
    paletted = opaque.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw = paletted.getpalette() or []
    colors = []
    for i in range(max_colors):
        base = i * 3
        if base + 2 < len(raw):
            colors.append((raw[base], raw[base + 1], raw[base + 2]))
    used = []
    for idx, (_, _, _, a) in zip(paletted.getdata(), img.getdata()):
        if a >= 32 and idx not in used:
            used.append(idx)
    return [colors[i] for i in used if i < len(colors)] or colors[:1]


def nearest(rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> int:
    best = 0
    best_dist = 10**9
    for i, color in enumerate(palette):
        dist = sum((rgb[c] - color[c]) ** 2 for c in range(3))
        if dist < best_dist:
            best = i
            best_dist = dist
    return best + 1


def sprite_payload(sprite: dict, img: Image.Image, source_name: str) -> dict:
    img = img.convert("RGBA").resize((32, 32), Image.Resampling.NEAREST)
    pal_rgb = quantized_palette(img)
    pixels = []
    for r, g, b, a in img.getdata():
        pixels.append(0 if a < 32 else nearest((r, g, b), pal_rgb))
    return {
        **sprite,
        "width": 32,
        "height": 32,
        "palette": ["#000000"] + [hex_color(c) for c in pal_rgb],
        "frames": [{
            "id": f"{sprite['id']}_openart_0",
            "name": f"CC0 {source_name}",
            "pixels": pixels,
        }],
    }


def classify(sprite: dict) -> tuple[str, str]:
    text = f"{sprite.get('id', '')} {sprite.get('name', '')}".lower()
    if any(w in text for w in ["lady", "beet", "bug", "mant", "moth", "bee", "fly", "gnat"]):
        if "lady" in text or "beet" in text:
            return "bug", "beetle"
        if "mant" in text:
            return "bug", "mantis"
        if "moth" in text:
            return "bug", "moth"
        if "bee" in text:
            return "bug", "bee"
        return "bug", "lady"
    if any(w in text for w in ["elephant", "rhino", "lion", "bird", "slime"]):
        return "bug", "animal"
    if any(w in text for w in ["tree", "house", "roof", "building"]):
        return "object", "house"
    if any(w in text for w in ["chest"]):
        return "object", "chest"
    if any(w in text for w in ["box", "match", "crate"]):
        return "object", "box"
    if any(w in text for w in ["sign", "jeep", "stack"]):
        return "object", "sign"
    if "poacher" in text:
        return "character", "poacher"
    if "ranger" in text:
        return "character", "ranger"
    if any(w in text for w in ["rival", "pip"]):
        return "character", "rival"
    if any(w in text for w in ["judge", "gran", "elder"]):
        return "character", "judge"
    if "robot" in text:
        return "character", "robot"
    if any(w in text for w in ["npc", "villager", "tulip"]):
        return "character", "npc"
    return "character", "hero"


def open_art_sprite(sprite: dict, index: int) -> dict:
    category, kind = classify(sprite)
    if category == "bug":
        sheet = BUG_SHEETS[kind]
        img = crop_bug(sheet)
        return sprite_payload(sprite, img, f"Ambient Insects / Puny {kind}")
    if category == "object":
        img = crop_object(kind)
        return sprite_payload(sprite, img, f"Puny object {kind}")
    sheet = CHARACTER_SHEETS[kind]
    img = crop_character(sheet, col=index % 3, row=0)
    return sprite_payload(sprite, img, f"Puny Characters {kind}")


def blank(fill: int) -> list[int]:
    return [fill] * (COLS * ROWS)


def scene_rect(paint: list[int], x: int, y: int, w: int, h: int, value: int) -> None:
    for yy in range(max(0, y), min(ROWS, y + h)):
        for xx in range(max(0, x), min(COLS, x + w)):
            paint[yy * COLS + xx] = value


def scatter(paint: list[int], coords: Iterable[tuple[int, int]], value: int) -> None:
    for x, y in coords:
        if 0 <= x < COLS and 0 <= y < ROWS:
            paint[y * COLS + x] = value


def enrich_scene(scene: dict, project_name: str) -> None:
    text = f"{project_name} {scene.get('id', '')} {scene.get('name', '')}".lower()
    if any(w in text for w in ["battle", "arena", "club"]):
        p = blank(12)
        scene_rect(p, 3, 3, 26, 20, 13)
        scene_rect(p, 5, 5, 22, 16, 3)
        scene_rect(p, 8, 8, 16, 10, 7)
        scene_rect(p, 11, 10, 10, 6, 11)
        scene_rect(p, 1, 23, 30, 3, 6)
        scatter(p, [(5, 4), (26, 4), (5, 21), (26, 21)], 14)
    elif any(w in text for w in ["dungeon", "cave", "hall"]):
        p = blank(12)
        scene_rect(p, 0, 0, COLS, 2, 11)
        scene_rect(p, 0, ROWS - 2, COLS, 2, 11)
        scene_rect(p, 0, 0, 2, ROWS, 11)
        scene_rect(p, COLS - 2, 0, 2, ROWS, 11)
        scene_rect(p, 6, 7, 20, 4, 13)
        scene_rect(p, 8, 17, 16, 4, 13)
        scatter(p, [(5, 5), (26, 5), (5, 22), (26, 22)], 14)
        scatter(p, [(14, 13), (15, 13), (16, 13), (17, 13)], 4)
    elif any(w in text for w in ["house", "interior", "room"]):
        p = blank(8)
        scene_rect(p, 0, 0, COLS, 3, 6)
        scene_rect(p, 0, ROWS - 4, COLS, 4, 6)
        scene_rect(p, 4, 5, 9, 6, 7)
        scene_rect(p, 19, 5, 8, 6, 7)
        scene_rect(p, 14, 17, 5, 7, 3)
        scene_rect(p, 15, 18, 3, 5, 9)
    else:
        p = blank(1)
        scene_rect(p, 13, 0, 5, ROWS, 3)
        scene_rect(p, 0, 12, COLS, 4, 3)
        scene_rect(p, 3, 4, 9, 8, 8)
        scene_rect(p, 4, 3, 7, 2, 7)
        scene_rect(p, 6, 7, 3, 3, 9)
        scene_rect(p, 21, 5, 8, 7, 8)
        scene_rect(p, 22, 4, 6, 2, 7)
        scene_rect(p, 24, 8, 3, 3, 9)
        scene_rect(p, 4, 20, 7, 4, 10)
        scene_rect(p, 23, 20, 5, 3, 10)
        scatter(p, [(2, 3), (28, 3), (2, 22), (29, 23), (7, 18), (20, 18)], 5)
        if any(w in text for w in ["patch", "garden"]):
            scatter(p, [(x, y) for x in range(3, 30, 3) for y in range(5, 23, 4)], 10)
    scene["paint_palette"] = SCENE_PALETTE
    scene["paint"] = p
    for actor in scene.get("actors", []):
        actor["x"] = max(0, min(224, int(actor.get("x", 0))))
        actor["y"] = max(0, min(192, int(actor.get("y", 0))))


def source_assets() -> list[dict]:
    return [
        {
            "id": "cc0_puny_characters",
            "name": "Puny Characters by Shade",
            "type": "sprite",
            "path": "https://opengameart.org/content/puny-characters",
            "notes": "CC0; embedded into template sprites by scripts/import_open_art_assets.py",
        },
        {
            "id": "cc0_puny_world",
            "name": "16x16 Puny World Tileset by Shade",
            "type": "background",
            "path": "https://opengameart.org/content/16x16-puny-world-tileset",
            "notes": "CC0; used as visual source for template scenes and objects",
        },
        {
            "id": "cc0_puny_dungeon",
            "name": "16x16 Puny Dungeon Tileset by Shade",
            "type": "background",
            "path": "https://opengameart.org/content/16x16-puny-dungeon-tileset",
            "notes": "CC0; used as visual source for dungeon scenes and objects",
        },
        {
            "id": "cc0_ambient_insects",
            "name": "Ambient Pixel Art Insects by madameberry",
            "type": "sprite",
            "path": "https://opengameart.org/content/ambient-pixel-art-insects",
            "notes": "CC0; embedded into Pocket Bugs creature sprites",
        },
    ]


def upgrade(path: Path) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for i, sprite in enumerate(data.get("sprites", [])):
        sprite.update(open_art_sprite(sprite, i))
    for scene in data.get("scenes", []):
        enrich_scene(scene, data.get("name", ""))
    existing = {asset.get("id") for asset in data.get("assets", [])}
    data.setdefault("assets", [])
    for asset in source_assets():
        if asset["id"] not in existing:
            data["assets"].append(asset)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Imported CC0 art into {path.relative_to(ROOT)}")


def main() -> None:
    ensure_sources()
    for path in PROJECTS:
        upgrade(path)


if __name__ == "__main__":
    main()
