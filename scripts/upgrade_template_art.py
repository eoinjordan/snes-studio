"""Upgrade bundled projects/templates to richer 32x32 16-bit style art.

The base templates started with deliberately tiny 16x16 placeholder sprites.
This pass keeps the existing game logic but replaces sprite frames and scene
paint with larger anime/16-bit inspired assets that read better in the editor
and in generated ROMs.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLS, ROWS = 32, 28


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


def canvas(fill: int = 0) -> list[int]:
    return [fill] * (32 * 32)


def pix(p: list[int], x: int, y: int, c: int) -> None:
    if 0 <= x < 32 and 0 <= y < 32:
        p[y * 32 + x] = c


def rect(p: list[int], x: int, y: int, w: int, h: int, c: int) -> None:
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            pix(p, xx, yy, c)


def ellipse(p: list[int], cx: int, cy: int, rx: int, ry: int, c: int) -> None:
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if ((x - cx) * (x - cx)) * ry * ry + ((y - cy) * (y - cy)) * rx * rx <= rx * rx * ry * ry:
                pix(p, x, y, c)


def line(p: list[int], x0: int, y0: int, x1: int, y1: int, c: int) -> None:
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pix(p, x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def anime_person(kind: str) -> tuple[list[str], list[int]]:
    palettes = {
        "hero": ["#000000", "#1b1b24", "#f3bd8e", "#b86b3a", "#3559b8", "#f4d35e", "#ffffff", "#2d7d5a", "#5b2c83"],
        "rival": ["#000000", "#24191e", "#f0b783", "#7c2f1d", "#c43636", "#f59e0b", "#ffffff", "#1c5f7a", "#4b5563"],
        "judge": ["#000000", "#20202a", "#f0bc8b", "#6b4a2c", "#334155", "#a855f7", "#ffffff", "#d8b46a", "#111827"],
        "ranger": ["#000000", "#1f2a1f", "#e7ad7d", "#70411f", "#2f7d46", "#d8b46a", "#ffffff", "#24412e", "#5d6b4a"],
        "poacher": ["#000000", "#231f20", "#e7ad7d", "#8f2d2d", "#4b5563", "#7c4a22", "#ffffff", "#2a2a2a", "#c2410c"],
        "robot": ["#000000", "#1f2937", "#d1d5db", "#60a5fa", "#facc15", "#ffffff", "#94a3b8", "#2563eb", "#111827"],
        "npc": ["#000000", "#211a24", "#f0bc8b", "#70411f", "#6d28d9", "#f4d35e", "#ffffff", "#2563eb", "#334155"],
    }
    pal = palettes.get(kind, palettes["npc"])
    p = canvas()
    # Hair and head outline
    ellipse(p, 16, 8, 8, 7, 1)
    ellipse(p, 16, 10, 7, 7, 2)
    rect(p, 9, 4, 14, 5, 3 if kind not in ("robot",) else 6)
    line(p, 9, 8, 6, 13, 1)
    line(p, 22, 8, 25, 13, 1)
    # Face
    rect(p, 12, 10, 3, 2, 1)
    rect(p, 18, 10, 3, 2, 1)
    pix(p, 15, 13, 3)
    rect(p, 14, 15, 5, 1, 1)
    pix(p, 13, 9, 6)
    pix(p, 19, 8, 6)
    # Body silhouette
    ellipse(p, 16, 21, 8, 8, 1)
    rect(p, 9, 17, 14, 11, 4)
    rect(p, 11, 18, 10, 3, 5)
    rect(p, 13, 17, 6, 12, 7 if kind in ("ranger", "hero") else 4)
    line(p, 9, 18, 5, 26, 1)
    line(p, 23, 18, 27, 26, 1)
    line(p, 10, 19, 6, 25, 2)
    line(p, 22, 19, 26, 25, 2)
    # Legs/boots
    rect(p, 11, 27, 4, 4, 8)
    rect(p, 18, 27, 4, 4, 8)
    rect(p, 10, 30, 6, 2, 1)
    rect(p, 17, 30, 6, 2, 1)
    return pal, p


def bug_sprite(kind: str) -> tuple[list[str], list[int]]:
    palettes = {
        "lady": ["#000000", "#1f1111", "#7f1d1d", "#dc2626", "#f87171", "#111827", "#facc15", "#ffffff", "#9ca3af"],
        "beetle": ["#000000", "#101827", "#1e1b4b", "#4338ca", "#818cf8", "#c4b5fd", "#facc15", "#ffffff", "#334155"],
        "mantis": ["#000000", "#102a16", "#166534", "#22c55e", "#86efac", "#fef08a", "#ffffff", "#365314", "#14532d"],
        "slime": ["#000000", "#064e3b", "#10b981", "#6ee7b7", "#d1fae5", "#ffffff", "#1f2937", "#34d399", "#047857"],
        "animal": ["#000000", "#31231a", "#6b4a2c", "#a16207", "#d6a35c", "#f8d99a", "#ffffff", "#3f3f46", "#92400e"],
    }
    pal = palettes.get(kind, palettes["animal"])
    p = canvas()
    if kind == "mantis":
        ellipse(p, 16, 15, 5, 11, 2)
        ellipse(p, 16, 12, 4, 8, 3)
        ellipse(p, 16, 7, 6, 5, 4)
        line(p, 12, 15, 4, 8, 2)
        line(p, 20, 15, 28, 8, 2)
        line(p, 11, 19, 3, 28, 1)
        line(p, 21, 19, 29, 28, 1)
        rect(p, 13, 6, 2, 2, 1)
        rect(p, 18, 6, 2, 2, 1)
    elif kind == "lady":
        ellipse(p, 16, 16, 11, 12, 1)
        ellipse(p, 16, 16, 9, 10, 3)
        rect(p, 15, 6, 2, 20, 1)
        ellipse(p, 12, 12, 2, 2, 5)
        ellipse(p, 20, 13, 2, 2, 5)
        ellipse(p, 11, 20, 2, 2, 5)
        ellipse(p, 21, 21, 2, 2, 5)
        ellipse(p, 16, 7, 7, 4, 5)
        rect(p, 12, 7, 2, 2, 6)
        rect(p, 19, 7, 2, 2, 6)
    elif kind == "beetle":
        ellipse(p, 16, 17, 10, 12, 1)
        ellipse(p, 16, 17, 8, 10, 3)
        ellipse(p, 16, 8, 6, 5, 2)
        line(p, 10, 6, 5, 2, 6)
        line(p, 22, 6, 27, 2, 6)
        line(p, 10, 20, 4, 28, 1)
        line(p, 22, 20, 28, 28, 1)
        rect(p, 15, 9, 2, 18, 1)
        pix(p, 12, 13, 7)
        pix(p, 20, 13, 7)
    elif kind == "slime":
        ellipse(p, 16, 19, 12, 9, 1)
        ellipse(p, 16, 18, 10, 8, 2)
        ellipse(p, 12, 15, 3, 3, 4)
        ellipse(p, 20, 15, 3, 3, 4)
        rect(p, 11, 20, 10, 2, 6)
        pix(p, 12, 14, 6)
        pix(p, 20, 14, 6)
    else:
        ellipse(p, 16, 18, 11, 8, 1)
        ellipse(p, 16, 18, 9, 6, 4)
        ellipse(p, 12, 13, 5, 4, 5)
        ellipse(p, 21, 14, 5, 4, 5)
        rect(p, 13, 12, 2, 2, 1)
        rect(p, 20, 12, 2, 2, 1)
        line(p, 8, 20, 4, 27, 1)
        line(p, 24, 20, 28, 27, 1)
    return pal, p


def object_sprite(kind: str) -> tuple[list[str], list[int]]:
    pal = ["#000000", "#2b1b12", "#7c3f18", "#c57930", "#f4d35e", "#fff7bc", "#7f1d1d", "#1f2937", "#94a3b8"]
    p = canvas()
    if kind == "robot":
        return anime_person("robot")
    if kind in ("sign", "chest", "box", "matchbox"):
        rect(p, 5, 10, 22, 15, 1)
        rect(p, 7, 12, 18, 11, 3)
        rect(p, 8, 13, 16, 3, 4)
        rect(p, 13, 17, 6, 3, 5)
        rect(p, 5, 24, 22, 3, 2)
        if kind == "sign":
            rect(p, 14, 24, 4, 7, 1)
            rect(p, 7, 8, 18, 10, 4)
            rect(p, 9, 10, 14, 6, 5)
    else:
        rect(p, 4, 12, 24, 14, 1)
        rect(p, 6, 14, 20, 10, 8)
        rect(p, 8, 16, 5, 5, 5)
        rect(p, 19, 16, 5, 5, 5)
        rect(p, 8, 25, 5, 3, 1)
        rect(p, 19, 25, 5, 3, 1)
    return pal, p


def classify(sprite: dict) -> str:
    sid = (sprite.get("id") or "").lower()
    name = (sprite.get("name") or "").lower()
    text = sid + " " + name
    if any(w in text for w in ["lady", "beetle", "bug", "manty", "mantis", "ant", "moth"]):
        if "lady" in text:
            return "lady"
        if "beet" in text:
            return "beetle"
        if "mant" in text:
            return "mantis"
        return "animal"
    if any(w in text for w in ["elephant", "rhino", "lion", "bird", "slime"]):
        return "slime" if "slime" in text else "animal"
    if any(w in text for w in ["rival", "pip", "poacher"]):
        return "poacher" if "poacher" in text else "rival"
    if any(w in text for w in ["judge", "gran", "villager", "npc", "tulip"]):
        return "judge" if "judge" in text else "npc"
    if any(w in text for w in ["ranger"]):
        return "ranger"
    if any(w in text for w in ["robot"]):
        return "robot"
    if any(w in text for w in ["chest", "box", "match", "sign", "jeep"]):
        return "object"
    return "hero"


def upgraded_sprite(sprite: dict) -> dict:
    kind = classify(sprite)
    if kind in {"lady", "beetle", "mantis", "slime", "animal"}:
        pal, px = bug_sprite(kind)
    elif kind == "object":
        pal, px = object_sprite("matchbox" if "box" in sprite.get("id", "").lower() else sprite.get("id", "").lower())
    else:
        pal, px = anime_person(kind)
    return {
        **sprite,
        "width": 32,
        "height": 32,
        "palette": pal,
        "frames": [{"id": f"{sprite['id']}_0", "name": "Frame 0", "pixels": px}],
    }


def blank_scene(fill: int) -> list[int]:
    return [fill] * (COLS * ROWS)


def scene_rect(p: list[int], x: int, y: int, w: int, h: int, c: int) -> None:
    for yy in range(max(0, y), min(ROWS, y + h)):
        for xx in range(max(0, x), min(COLS, x + w)):
            p[yy * COLS + xx] = c


def enrich_scene(scene: dict, project_name: str) -> None:
    name = (scene.get("name") or scene.get("id") or "").lower()
    sid = (scene.get("id") or "").lower()
    text = f"{project_name} {name} {sid}".lower()
    if any(w in text for w in ["battle", "arena", "club"]):
        pal = ["#162033", "#31425f", "#586f8e", "#d9b45f", "#e8d784", "#73433a", "#f7f0cf", "#28303d"]
        p = blank_scene(1)
        scene_rect(p, 3, 3, 26, 20, 2)
        scene_rect(p, 6, 6, 20, 14, 3)
        scene_rect(p, 8, 8, 16, 10, 4)
        scene_rect(p, 11, 10, 10, 6, 1)
        scene_rect(p, 2, 22, 28, 3, 7)
    elif any(w in text for w in ["town", "garden", "savannah", "patch", "station"]):
        pal = ["#2d7d46", "#4da85a", "#82c66f", "#cfae63", "#8b5a3c", "#b64040", "#f3d47a", "#5c7fa6", "#f6efe0"]
        p = blank_scene(1)
        scene_rect(p, 14, 0, 4, ROWS, 3)
        scene_rect(p, 0, 13, COLS, 3, 3)
        scene_rect(p, 3, 4, 8, 7, 4)
        scene_rect(p, 4, 3, 6, 2, 5)
        scene_rect(p, 5, 6, 2, 2, 8)
        scene_rect(p, 8, 6, 2, 2, 8)
        scene_rect(p, 22, 5, 7, 7, 4)
        scene_rect(p, 23, 4, 5, 2, 5)
        scene_rect(p, 24, 7, 3, 3, 8)
        scene_rect(p, 4, 20, 7, 4, 6)
        scene_rect(p, 23, 20, 5, 3, 6)
    elif any(w in text for w in ["house", "interior", "room"]):
        pal = ["#6b4932", "#8a6040", "#c58b53", "#e8c17a", "#49301f", "#9b5c35", "#f3e1b0", "#34506b"]
        p = blank_scene(1)
        scene_rect(p, 0, 0, COLS, 3, 4)
        scene_rect(p, 0, ROWS - 3, COLS, 3, 4)
        scene_rect(p, 4, 5, 8, 5, 2)
        scene_rect(p, 20, 5, 7, 6, 2)
        scene_rect(p, 14, 18, 5, 7, 3)
        scene_rect(p, 15, 19, 3, 5, 6)
        scene_rect(p, 6, 15, 8, 3, 5)
    elif any(w in text for w in ["dungeon", "cave", "hall"]):
        pal = ["#303446", "#45495f", "#686f87", "#b8684a", "#f2c66d", "#1e2230", "#8d95ad", "#2a2d3e"]
        p = blank_scene(0)
        scene_rect(p, 0, 0, COLS, 2, 5)
        scene_rect(p, 0, ROWS - 2, COLS, 2, 5)
        scene_rect(p, 0, 0, 2, ROWS, 5)
        scene_rect(p, COLS - 2, 0, 2, ROWS, 5)
        scene_rect(p, 6, 6, 4, 6, 2)
        scene_rect(p, 22, 6, 4, 6, 2)
        scene_rect(p, 8, 17, 16, 3, 6)
        scene_rect(p, 5, 4, 2, 2, 4)
        scene_rect(p, 25, 4, 2, 2, 4)
    else:
        pal = ["#2f6f58", "#4d9b6f", "#7ac27d", "#b99c61", "#6f4e37", "#d6b45f", "#e9e0bb", "#456b90"]
        p = blank_scene(1)
        scene_rect(p, 14, 0, 4, ROWS, 3)
        scene_rect(p, 0, 12, COLS, 4, 3)
        scene_rect(p, 5, 5, 8, 6, 4)
        scene_rect(p, 6, 4, 6, 2, 5)
        scene_rect(p, 21, 17, 7, 6, 4)
        scene_rect(p, 22, 16, 5, 2, 5)
    scene["paint_palette"] = pal
    scene["paint"] = p
    for actor in scene.get("actors", []):
        actor["x"] = max(0, min(224, int(actor.get("x", 0))))
        actor["y"] = max(0, min(192, int(actor.get("y", 0))))


def upgrade(path: Path) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for sprite in data.get("sprites", []):
        sprite.update(upgraded_sprite(sprite))
    pname = data.get("name", "")
    for scene in data.get("scenes", []):
        enrich_scene(scene, pname)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Upgraded {path.relative_to(ROOT)}")


def main() -> None:
    for path in PROJECTS:
        upgrade(path)


if __name__ == "__main__":
    main()
