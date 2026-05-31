"""Give bundled example scenes real tile-based backgrounds (Zelda/Pokemon style).

Authors a few themed 16x14 overworld tilemaps from the bundled tileset and
applies them to the example projects so the showcase ROM and editor demonstrate
the tile background feature. Deterministic (no RNG) so builds are reproducible.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLS, ROWS = 16, 14
TILESET = json.loads((ROOT / "snesstudio" / "assets" / "bg_overworld.json").read_text(encoding="utf-8"))
IDX = {t["id"]: i for i, t in enumerate(TILESET["tiles"])}


def blank(fill: str) -> list[int]:
    return [IDX[fill]] * (COLS * ROWS)


def put(m, c, r, tile):
    if 0 <= c < COLS and 0 <= r < ROWS:
        m[r * COLS + c] = IDX[tile]


def border(m, edge):
    for c in range(COLS):
        put(m, c, 0, edge); put(m, c, ROWS - 1, edge)
    for r in range(ROWS):
        put(m, 0, r, edge); put(m, COLS - 1, r, edge)


def garden() -> list[int]:
    m = blank("grass")
    border(m, "tree")
    for r in range(4, 7):                       # pond
        for c in range(2, 6):
            put(m, c, r, "water")
    for r in range(1, ROWS - 1):                # path
        put(m, 8, r, "sand")
    for (c, r) in [(11, 3), (12, 4), (13, 5), (11, 9), (13, 10), (3, 9), (2, 10)]:
        put(m, c, r, "flowers")
    for (c, r) in [(12, 2), (10, 6), (4, 2), (13, 8), (6, 10)]:
        put(m, c, r, "bush")
    return m


def arena() -> list[int]:
    m = blank("sand")
    border(m, "fence_stone")
    for r in range(2, ROWS - 2):                # grass infield
        for c in range(2, COLS - 2):
            put(m, c, r, "grass")
    for (c, r) in [(4, 4), (11, 4), (4, 9), (11, 9)]:
        put(m, c, r, "rock")
    for (c, r) in [(7, 6), (8, 6), (7, 7), (8, 7)]:
        put(m, c, r, "flowers")
    return m


def meadow() -> list[int]:
    m = blank("grass")
    border(m, "fence_wood")
    for c in range(COLS):                        # sand strip along the bottom
        put(m, c, ROWS - 2, "sand")
    for (c, r) in [(3, 3), (6, 5), (9, 3), (12, 6), (4, 8), (10, 9), (13, 4)]:
        put(m, c, r, "bush")
    for (c, r) in [(5, 4), (8, 7), (11, 5), (3, 9)]:
        put(m, c, r, "flowers")
    return m


THEMES = [garden(), arena(), meadow()]

# project -> per-scene-index theme (cycled)
PROJECTS = {
    "pocket-bugs": [garden(), arena(), garden(), meadow(), garden(), arena()],
    "poachermon": [meadow(), garden(), meadow(), arena(), garden()],
}


def apply(slug: str, themes: list[list[int]]) -> None:
    for rel in (f"examples/{slug}/project.snesproj", f"web/public/examples/{slug}.snesproj"):
        path = ROOT / rel
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for i, scene in enumerate(data.get("scenes", [])):
            scene["tilemap"] = themes[i % len(themes)]
            scene["tileset"] = "overworld"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("tiled", rel, f'({len(data.get("scenes", []))} scenes)')


def main() -> None:
    for slug, themes in PROJECTS.items():
        apply(slug, themes)


if __name__ == "__main__":
    main()
