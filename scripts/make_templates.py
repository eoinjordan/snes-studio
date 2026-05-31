"""Generate the SNES Studio template gallery: complete, polished starter games
that show off painted tile backgrounds + scene-to-scene jumps.

Writes web/public/templates/<id>.snesproj and templates/index.json. Run from repo
root:  python scripts/make_templates.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from snesstudio.schema import Project, model_to_jsonable  # noqa: E402

COLS, ROWS = 32, 28
CW, CH = 256 // COLS, 224 // ROWS


def _rnd(c, r, s=0):
    x = math.sin((c + 1) * 12.9898 + (r + 1) * 78.233 + s) * 43758.5453
    return x - math.floor(x)


def grid(fn):
    return [fn(c, r) for r in range(ROWS) for c in range(COLS)]


def _border(c, r):
    return c == 0 or r == 0 or c == COLS - 1 or r == ROWS - 1


def walls(paint, solid):
    """Greedy 2D rectangle merge of solid cells -> few clean collision rects."""
    s = set(solid)
    used = [[False] * COLS for _ in range(ROWS)]
    def free(c, r):
        return 0 <= c < COLS and 0 <= r < ROWS and paint[r * COLS + c] in s and not used[r][c]
    rects = []
    for r in range(ROWS):
        for c in range(COLS):
            if not free(c, r):
                continue
            w = 1
            while free(c + w, r):
                w += 1
            h = 1
            while r + h < ROWS and all(free(c + i, r + h) for i in range(w)):
                h += 1
            for rr in range(r, r + h):
                for cc in range(c, c + w):
                    used[rr][cc] = True
            rects.append({"x": c * CW, "y": r * CH, "w": w * CW, "h": h * CH})
    return rects


# --- preset backgrounds (ported from the web editor) --------------------------
def bg_grassland():
    pal = ["#5aa83a", "#48902f", "#caa15a", "#2f7fd1", "#e8d24a"]
    midL, midR = (COLS // 2) - 1, COLS // 2
    def f(c, r):
        if midL <= c <= midR: return 2
        if r >= ROWS - 6 and c >= COLS - 8: return 3
        if _rnd(c, r) > 0.86: return 4
        return 1 if _rnd(c, r, 9) > 0.7 else 0
    return grid(f), pal, [3]


def bg_cave():
    # index 2 = wall (solid, structural border only); 1/4 = decorative floor (non-solid)
    pal = ["#3a352f", "#23201c", "#5a5048", "#7a6a55", "#100d0b"]
    def f(c, r):
        if _border(c, r): return 2
        if _rnd(c, r, 7) > 0.95: return 4
        return 1 if _rnd(c, r, 1) > 0.82 else 0
    return grid(f), pal, [2]


def bg_dungeon():
    # structural walls: border + two interior pillars; rest decorative (non-solid)
    pal = ["#4b4f63", "#2e3142", "#8a8fae", "#b34a3a", "#1a1c26"]
    def f(c, r):
        if _border(c, r): return 2
        if 6 <= r <= 9 and (c == 10 or c == 21): return 2   # pillars
        if _rnd(c, r, 6) > 0.96: return 3                    # torches (decor)
        return 4 if _rnd(c, r, 4) > 0.85 else 0
    return grid(f), pal, [2]


def bg_town():
    pal = ["#5aa83a", "#caa15a", "#9b6b43", "#b34a3a", "#8a8a8a"]
    def f(c, r):
        if 14 <= c <= 17: return 1
        if 13 <= r <= 15: return 1
        if 3 <= r <= 7 and 4 <= c <= 9: return 3 if r <= 4 else 2
        if 3 <= r <= 7 and 22 <= c <= 27: return 3 if r <= 4 else 2
        return 4 if _rnd(c, r, 8) > 0.85 else 0
    return grid(f), pal, [2, 3]


def bg_interior():
    pal = ["#7a5436", "#4a321f", "#caa15a", "#9b6b43", "#2a1c10"]
    def f(c, r):
        if _border(c, r): return 1
        if r == ROWS - 2 and 14 <= c <= 17: return 2
        return 3 if _rnd(c, r, 2) > 0.9 else 0
    return grid(f), pal, [1]


# --- sprites (16x16 ASCII over a per-sprite palette) ---------------------------
def art(rows):
    px = []
    for row in rows:
        assert len(row) == 16, (len(row), row)
        for ch in row:
            px.append(0 if ch in ". " else int(ch, 16))
    assert len(px) == 256
    return px


HERO = art([
    "................",
    "....111111......",
    "...12222221.....",
    "...12133121.....",
    "...12222221.....",
    "....122221......",
    "....144441......",
    "...14444441.....",
    "...44444444.....",
    "...14444441.....",
    "....144441......",
    "....14..41......",
    "....55..55......",
    "....55..55......",
    "....33..33......",
    "................",
])
SLIME = art([
    "................",
    "................",
    "......1111......",
    ".....122221.....",
    "....12222221....",
    "...1222222221...",
    "..122112211221..",
    "..123113311321..",
    "..122222222221..",
    "..122222222221..",
    "..122222222221..",
    "...1222222221...",
    "....12222221....",
    ".....1.11.1.....",
    "................",
    "................",
])
NPC = art([
    "................",
    "....111111......",
    "...12222221.....",
    "...12133121.....",
    "...12222221.....",
    "....122221......",
    "....133331......",
    "...13333331.....",
    "...33333333.....",
    "...13333331.....",
    "....133331......",
    "....13333.1.....",
    "....33..33......",
    "....33..33......",
    "....22..22......",
    "................",
])
CHEST = art([
    "................",
    "................",
    "................",
    "...1111111111...",
    "..133333333331..",
    "..132222222231..",
    "..132444444231..",
    "..132422224231..",
    "..132444444231..",
    "..132222222231..",
    "..133333333331..",
    "...1111111111...",
    "................",
    "................",
    "................",
    "................",
])


def sprite(sid, name, palette, pixels):
    return {"id": sid, "name": name, "width": 16, "height": 16, "palette": palette,
            "frames": [{"id": f"{sid}_0", "name": "Frame 0", "pixels": pixels}]}


HERO_S = lambda sid="hero", name="Hero": sprite(sid, name, ["#000000", "#1f2937", "#f1c08a", "#3f6e2e", "#caa15a"], HERO)
SLIME_S = sprite("slime", "Slime", ["#000000", "#14532d", "#4ade80", "#bbf7d0"], SLIME)
NPC_S = sprite("npc", "Villager", ["#000000", "#1f2937", "#f1c08a", "#6d28d9"], NPC)
CHEST_S = sprite("chest", "Treasure Chest", ["#000000", "#5a3a1a", "#caa15a", "#fcd34d", "#92400e"], CHEST)


def scene(sid, name, bg, actors, triggers=None):
    paint, pal, solid = bg
    cols = [{"id": f"{sid}_w{i}", **rect} for i, rect in enumerate(walls(paint, solid))]
    return {"id": sid, "name": name, "paint": paint, "paint_palette": pal,
            "actors": actors, "triggers": triggers or [], "collision": cols}


def actor(sid, name, x, y, spr, interact=None):
    a = {"id": sid, "name": name, "x": x, "y": y, "sprite": spr}
    if interact:
        a["events"] = {"interact": interact}
    return a


def door(tid, name, x, y, w, h, event):
    return {"id": tid, "name": name, "x": x, "y": y, "w": w, "h": h, "event": event}


def goto(cid, name, kind, key, target):
    trig = {"type": kind}
    trig["zone" if kind == "zone_enter" else "actor"] = key
    return {"id": cid, "name": name, "trigger": trig,
            "steps": [{"id": f"{cid}_go", "type": "change_scene", "scene": target}]}


def say(cid, name, kind, key, lines, scene_id=None):
    trig = {"type": kind}
    if kind == "scene_start":
        trig["scene"] = scene_id
    elif kind == "actor_interact":
        trig["actor"] = key
    steps = [{"id": f"{cid}_{i}", "type": "show_text", "text": t} for i, t in enumerate(lines)]
    return {"id": cid, "name": name, "trigger": trig, "steps": steps}


# --- Template 1: Dungeon Escape -----------------------------------------------
def dungeon_escape():
    return {
        "schema_version": "1.0", "name": "Dungeon Escape", "target": "snes",
        "rom": {"title": "DUNGEON ESCAPE", "region": "NTSC"},
        "flags": {}, "variables": {"loot": 0},
        "sprites": [HERO_S(), SLIME_S, CHEST_S],
        "scenes": [
            scene("entrance", "Cave Entrance", bg_cave(),
                  [actor("hero", "Hero", 40, 110, "hero")],
                  [door("d_hall", "Deeper in", 232, 96, 24, 48, "to_hall")]),
            scene("hall", "Dungeon Hall", bg_dungeon(),
                  [actor("hero2", "Hero", 40, 110, "hero"),
                   actor("slime", "Slime", 150, 90, "slime", "slime_talk")],
                  [door("d_back", "Back", 0, 96, 16, 48, "to_entrance"),
                   door("d_treasure", "Onward", 232, 96, 24, 48, "to_treasure")]),
            scene("treasure", "Treasure Room", bg_dungeon(),
                  [actor("hero3", "Hero", 40, 150, "hero"),
                   actor("chest", "Chest", 130, 90, "chest", "open_chest")],
                  [door("d_hall2", "Back", 0, 96, 16, 48, "to_hall")]),
        ],
        "eventChains": [
            say("intro", "Trapped!", "scene_start", None, ["The gate slams shut!", "Find a way out of the dungeon."], "entrance"),
            goto("to_hall", "To the Hall", "zone_enter", "d_hall", "hall"),
            goto("to_entrance", "Back to Entrance", "zone_enter", "d_back", "entrance"),
            goto("to_treasure", "To the Treasure", "zone_enter", "d_treasure", "treasure"),
            goto("to_hall2", "Back to the Hall", "zone_enter", "d_hall2", "hall"),
            say("slime_talk", "Slime", "actor_interact", "slime", ["Slime: Blub! (It wobbles aside.)"]),
            say("open_chest", "Open Chest", "actor_interact", "chest", ["You found the lost crown!", "Escape complete. You win!"]),
        ],
    }


# --- Template 2: Town Tales ----------------------------------------------------
def town_tales():
    return {
        "schema_version": "1.0", "name": "Town Tales", "target": "snes",
        "rom": {"title": "TOWN TALES", "region": "NTSC"},
        "flags": {}, "variables": {},
        "sprites": [HERO_S(), NPC_S],
        "scenes": [
            scene("town", "Town Square", bg_town(),
                  [actor("hero", "Hero", 130, 200, "hero"),
                   actor("villager", "Villager", 70, 180, "npc", "villager_talk")],
                  [door("d_house", "Your house", 64, 64, 48, 24, "enter_house")]),
            scene("house", "Your House", bg_interior(),
                  [actor("hero2", "Hero", 128, 180, "hero"),
                   actor("gran", "Gran", 90, 90, "npc", "gran_talk")],
                  [door("d_out", "Outside", 112, 200, 32, 24, "leave_house")]),
        ],
        "eventChains": [
            say("town_intro", "A new day", "scene_start", None, ["Welcome to Maple Town!", "Talk to people and explore."], "town"),
            goto("enter_house", "Enter House", "zone_enter", "d_house", "house"),
            goto("leave_house", "Go Outside", "zone_enter", "d_out", "town"),
            say("villager_talk", "Villager", "actor_interact", "villager", ["Villager: The market opens at noon."]),
            say("gran_talk", "Gran", "actor_interact", "gran", ["Gran: Welcome home, dear! Tea?"]),
        ],
    }


GALLERY = [
    {"id": "poachermon", "name": "Poachermon", "file": "examples/poachermon.snesproj",
     "description": "Comedic savannah safari: rescue wild creatures from a poacher across 5 scenes."},
    {"id": "dungeon-escape", "name": "Dungeon Escape", "build": dungeon_escape,
     "description": "Top-down dungeon crawl. Walk through doors to jump between 3 connected rooms."},
    {"id": "town-tales", "name": "Town Tales", "build": town_tales,
     "description": "A cosy town with an enterable house. Chat to villagers; doors link the scenes."},
]


def main():
    out = ROOT / "web" / "public" / "templates"
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for t in GALLERY:
        entry = {"id": t["id"], "name": t["name"], "description": t["description"]}
        if "build" in t:
            data = model_to_jsonable(Project.model_validate(t["build"]()))
            (out / f"{t['id']}.snesproj").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            entry["file"] = f"templates/{t['id']}.snesproj"
            print(f"Wrote {out / (t['id'] + '.snesproj')}  scenes={[s['id'] for s in data['scenes']]}")
        else:
            entry["file"] = t["file"]
        index.append(entry)
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out / 'index.json'} with {len(index)} templates")


if __name__ == "__main__":
    main()
