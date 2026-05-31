"""Import listed OpenGameArt packs into bundled projects/templates.

Primary sources requested for this art pass:
- 16xx16 Tileset (Pokemon/Zelda style:D) by Damian Gasinski aka Gassasin, CC-BY 3.0
- A Battle Theme (165 BPM) by Wanwaka, CC-BY 4.0
- Tuxemon tileset by Buch, CC-BY-SA 3.0
- Retro Tileset by Paul Barden / Damian Gasinski aka Gassasin, CC-BY 3.0
- RPGui HUD - Asset Pack by Narehop, CC-BY 4.0
- Tiny16 Tileset by Fuwaneko Games, CC-BY 3.0

OPMon Center is intentionally not embedded: its OGA page lists GPL 3.0 and
contains a public licensing/trademark concern in the comments. Pocket Bugs bug
creatures still use Ambient Pixel Art Insects by madameberry, CC0, because the
requested list is tile/UI/music heavy and does not contain bug creature sheets.
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
CACHE = ROOT / "build" / "assetpacks" / "listed"
BUG_CACHE = ROOT / "build" / "assetpacks" / "cutebugs"
COLS, ROWS = 32, 28

SOURCES = {
    "gassasin_pokemonzelda": {
        "url": "https://opengameart.org/sites/default/files/16x16RetroTileset.zip",
        "file": CACHE / "gassasin-retro.zip",
        "dir": CACHE / "gassasin-retro",
    },
    "battle_165": {
        "url": "https://opengameart.org/sites/default/files/battle_165.wav",
        "file": CACHE / "battle_165.wav",
    },
    "tuxemon_tileset": {
        "url": "https://opengameart.org/sites/default/files/sheet_6.png",
        "file": CACHE / "tuxemon-sheet.png",
    },
    "retro_tileset": {
        "url": "https://opengameart.org/sites/default/files/tilesets_7.zip",
        "file": CACHE / "retro-tilesets.zip",
        "dir": CACHE / "retro-tilesets",
    },
    "rpgui_hud": {
        "url": "https://opengameart.org/sites/default/files/RPGui_free_1.png",
        "file": CACHE / "rpgui-free.png",
    },
    "tiny16": {
        "url": "https://opengameart.org/sites/default/files/tiny-16.png",
        "file": CACHE / "tiny-16.png",
    },
    "ambient_insects": {
        "url": "https://opengameart.org/sites/default/files/cutebugs_by_madameberry.zip",
        "file": ROOT / "build" / "assetpacks" / "cutebugs_by_madameberry.zip",
        "dir": BUG_CACHE,
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

ROLE_TINTS = {
    "hero": (54, 112, 214),
    "rival": (209, 61, 68),
    "judge": (139, 83, 188),
    "ranger": (57, 139, 75),
    "poacher": (104, 77, 58),
    "robot": (78, 164, 184),
    "npc": (222, 159, 71),
}

BUG_SHEETS = {
    "lady": "beetle.png",
    "beetle": "beetle.png",
    "mantis": "dragonfly.png",
    "moth": "moth.png",
    "bee": "bee.png",
    "slime": "gnat.png",
    # No real wildlife art ships in the CC0 insect pack, so each animal role is
    # mapped to a DISTINCT insect sheet — keeps every sprite unique and readable
    # instead of every animal collapsing onto one shared "moth" image.
    "elephant": "moth.png",
    "rhino": "beetle.png",
    "lion": "bee.png",
    "bird": "dragonfly.png",
    "monkey": "firefly.png",
    "animal": "gnat.png",
}

# Source rectangles are tile coordinates in 16px cells unless noted otherwise.
OBJECT_RECTS = {
    "house": (CACHE / "gassasin-retro" / "PokemonLike.png", 2, 0, 2, 2),
    "tree": (CACHE / "tuxemon-sheet.png", 3, 1, 2, 2),
    "sign": (CACHE / "tiny-16.png", 0, 0, 1, 1),
    "box": (CACHE / "rpgui-free.png", 0, 0, 2, 1),
    "matchbox": (CACHE / "rpgui-free.png", 0, 0, 2, 1),
    "chest": (CACHE / "gassasin-retro" / "PokemonLike.png", 10, 0, 1, 1),
    "jeep": (CACHE / "retro-tilesets" / "Outside_B.png", 9, 4, 2, 2),
    "stone": (CACHE / "tuxemon-sheet.png", 0, 0, 2, 2),
}

SCENE_PALETTE = [
    "#141414", "#65b747", "#9ed45c", "#cda761", "#4593ad", "#2f7838",
    "#8d6230", "#d9bf68", "#dcd4ae", "#fff4c2", "#d94e38", "#29313a",
    "#6a706b", "#b7bdad", "#e58a56", "#ffffff",
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


def fit_to_32(img: Image.Image, margin: int = 0) -> Image.Image:
    img = img.convert("RGBA")
    box = img.getchannel("A").getbbox()
    if not box:
        return Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    crop = img.crop(box)
    max_side = 32 - margin * 2
    scale = min(max_side / crop.width, max_side / crop.height)
    if crop.width <= 16 and crop.height <= 16:
        scale = max(1, int(scale))
    nw = max(1, min(max_side, int(crop.width * scale)))
    nh = max(1, min(max_side, int(crop.height * scale)))
    resized = crop.resize((nw, nh), Image.Resampling.NEAREST)
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    out.alpha_composite(resized, ((32 - nw) // 2, 32 - nh - 1))
    return out


def tint_character(img: Image.Image, tint: tuple[int, int, int]) -> Image.Image:
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pixels = []
    for r, g, b, a in img.getdata():
        if a < 32:
            pixels.append((0, 0, 0, 0))
            continue
        # Preserve skin and dark outlines; tint clothing/hair enough to make roles distinct.
        is_skin = r > 135 and 70 < g < 150 and b < 120
        is_outline = r < 45 and g < 45 and b < 45
        if is_skin or is_outline:
            pixels.append((r, g, b, a))
        else:
            pixels.append(((r + tint[0]) // 2, (g + tint[1]) // 2, (b + tint[2]) // 2, a))
    out.putdata(pixels)
    return out


def character_image(kind: str, variant: int) -> Image.Image:
    # Idle frames 0/1/3 share one silhouette; only frame 2 differs. Alternate
    # between the two distinct silhouettes and mirror every other pair so that
    # characters with the same role tint still get a unique shape.
    frame = 2 if variant % 2 else 0
    path = CACHE / "gassasin-retro" / "CharacterAnimation" / "Idle" / f"Untitled-0_{frame}.png"
    img = rgba(path)
    if (variant // 2) % 2:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return fit_to_32(tint_character(img, ROLE_TINTS[kind]), margin=1)


def bug_image(kind: str) -> Image.Image:
    sheet = BUG_SHEETS[kind]
    return fit_to_32(rgba(BUG_CACHE / sheet), margin=2)


def object_image(kind: str) -> Image.Image:
    path, tx, ty, tw, th = OBJECT_RECTS.get(kind, OBJECT_RECTS["box"])
    src = rgba(path)
    crop = src.crop((tx * 16, ty * 16, (tx + tw) * 16, (ty + th) * 16))
    return fit_to_32(crop, margin=0)


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
            "id": f"{sprite['id']}_listed_openart_0",
            "name": f"OpenGameArt {source_name}",
            "pixels": pixels,
        }],
    }


def classify(sprite: dict) -> tuple[str, str]:
    text = f"{sprite.get('id', '')} {sprite.get('name', '')}".lower()
    # Protagonist guard: the player is a person, not a creature. Names like
    # "You (Bug Tamer)" contain "bug" and would otherwise be drawn as a beetle.
    if any(w in text for w in ["player", "tamer", "protagonist", "hero", "you ("]):
        return "character", "hero"
    if any(w in text for w in ["lady", "beet", "bug", "mant", "moth", "bee", "fly", "gnat"]):
        if "mant" in text:
            return "bug", "mantis"
        if "moth" in text:
            return "bug", "moth"
        if "bee" in text:
            return "bug", "bee"
        return "bug", "beetle"
    # Each animal role maps to its own distinct insect sheet (see BUG_SHEETS).
    for kind in ["elephant", "rhino", "lion", "bird", "monkey", "slime"]:
        if kind in text:
            return "bug", kind
    if any(w in text for w in ["house", "roof", "building"]):
        return "object", "house"
    if "chest" in text:
        return "object", "chest"
    if any(w in text for w in ["box", "match", "crate", "stack"]):
        return "object", "matchbox"
    if any(w in text for w in ["sign"]):
        return "object", "sign"
    if "jeep" in text:
        return "object", "jeep"
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
    if any(w in text for w in ["npc", "villager", "tulip", "barkeep", "captain"]):
        return "character", "npc"
    return "character", "hero"


def open_art_sprite(sprite: dict, index: int) -> dict:
    category, kind = classify(sprite)
    if category == "bug":
        return sprite_payload(sprite, bug_image(kind), f"Ambient Insects {kind}")
    if category == "object":
        return sprite_payload(sprite, object_image(kind), f"listed tileset object {kind}")
    return sprite_payload(sprite, character_image(kind, index), f"16xx16 Pokemon/Zelda character {kind}")


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
        scene_rect(p, 10, 9, 12, 8, 11)
        scene_rect(p, 1, 23, 30, 3, 6)
        scatter(p, [(4, 4), (27, 4), (4, 21), (27, 21)], 14)
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
        {"id": "oga_gassasin_pokemonzelda", "name": "16xx16 Tileset (Pokemon/Zelda style:D) by Damian Gasinski aka Gassasin", "type": "sprite", "path": "https://opengameart.org/content/16xx16-tileset-pokemonzelda-styled", "notes": "CC-BY 3.0; character/object source for bundled templates"},
        {"id": "oga_battle_165", "name": "A Battle Theme (165 BPM) by Wanwaka", "type": "music", "path": "https://opengameart.org/content/a-battle-theme-165-bpm", "notes": "CC-BY 4.0; battle music source metadata"},
        {"id": "oga_tuxemon_tileset", "name": "Tuxemon tileset by Buch", "type": "background", "path": "https://opengameart.org/content/tuxemon-tileset", "notes": "CC-BY-SA 3.0; tile/object source for bundled templates"},
        {"id": "oga_retro_tileset", "name": "Retro Tileset by Paul Barden / Damian Gasinski aka Gassasin", "type": "background", "path": "https://opengameart.org/content/retro-tileset", "notes": "CC-BY 3.0; map/object source for bundled templates"},
        {"id": "oga_rpgui_hud", "name": "RPGui HUD - Asset Pack by Narehop", "type": "other", "path": "https://opengameart.org/content/rpgui-hud-asset-pack", "notes": "CC-BY 4.0; UI and battle box source"},
        {"id": "oga_tiny16", "name": "Tiny16 Tileset by Fuwaneko Games", "type": "background", "path": "https://opengameart.org/content/tiny16-tileset", "notes": "CC-BY 3.0; town/sign source for bundled templates"},
        {"id": "cc0_ambient_insects", "name": "Ambient Pixel Art Insects by madameberry", "type": "sprite", "path": "https://opengameart.org/content/ambient-pixel-art-insects", "notes": "CC0; creature source for Pocket Bugs"},
        {"id": "skipped_opmon_center", "name": "OPMon Center by Navet56", "type": "other", "path": "https://opengameart.org/content/opmon-center", "notes": "Not embedded: GPL 3.0 and public page comments flag Pokemon/trademark licensing concerns"},
    ]


def upgrade(path: Path) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for i, sprite in enumerate(data.get("sprites", [])):
        sprite.update(open_art_sprite(sprite, i))
    for scene in data.get("scenes", []):
        enrich_scene(scene, data.get("name", ""))
    data["assets"] = [a for a in data.get("assets", []) if not str(a.get("id", "")).startswith(("cc0_puny", "oga_", "skipped_opmon_center"))]
    existing = {asset.get("id") for asset in data["assets"]}
    for asset in source_assets():
        if asset["id"] not in existing:
            data["assets"].append(asset)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Imported listed OGA art into {path.relative_to(ROOT)}")


def main() -> None:
    ensure_sources()
    for path in PROJECTS:
        upgrade(path)


if __name__ == "__main__":
    main()
