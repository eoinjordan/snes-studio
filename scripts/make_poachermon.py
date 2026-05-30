"""Generate the Poachermon launch-template project.

Poachermon — "Gotta Save 'Em All!" — is the flagship example game that ships
with SNES Studio. It's a comedic African-savannah safari: you're a park ranger
who sets camera traps, rescues wild creatures (the "poachermon": elephant,
rhino, lion cub, bird) and chases a red-capped poacher across the reserve.

The story beats and dry, witty tone are taken from the author's GB Studio
"Rangers of the Wild: Poachers on Parade" project (Professor Tulip, camera
traps, "The Throttle of Justice"). Sprites are authored as 16x16 ASCII art over
a per-sprite palette, so the pixel data stays human-readable and reviewable.

Each art row is exactly 16 characters. '.' is transparent (palette index 0);
the hex digits 1-9 / a-f map to palette indices 1..15. Run from the repo root:

    python scripts/make_poachermon.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from snesstudio.schema import Project, model_to_jsonable  # noqa: E402


def art(rows: list[str]) -> list[int]:
    """Parse 16 rows of 16 chars into palette indices ('.'=0, hex digit otherwise)."""
    assert len(rows) == 16, f"expected 16 rows, got {len(rows)}"
    pixels: list[int] = []
    for row in rows:
        assert len(row) == 16, f"expected 16 cols, got {len(row)}: {row!r}"
        for ch in row:
            pixels.append(0 if ch in "." " " else int(ch, 16))
    return pixels


# --- Player: park ranger (brown hair, green vest, tan skin) ----------------
RANGER = art([
    "................",
    "....111111......",
    "...13333331.....",
    "...32222223.....",
    "...32122123.....",
    "...32222223.....",
    "....322223......",
    "....444444......",
    "...54444445.....",
    "...54444445.....",
    "...54444445.....",
    "....444444......",
    "....555555......",
    "....55..55......",
    "....55..55......",
    "....33..33......",
])

# --- Antagonist: poacher (red cap, grey jacket) ---------------------------
POACHER = art([
    "................",
    "....333333......",
    "...33333333.....",
    "...32222223.....",
    "...32122123.....",
    "...32222223.....",
    "....322223......",
    "....444444......",
    "...44444444.....",
    "...44444444.....",
    "...44444444.....",
    "....444444......",
    "....544445......",
    "....55..55......",
    "....55..55......",
    "....55..55......",
])

# --- Safari jeep (green) ---------------------------------------------------
JEEP = art([
    "................",
    "................",
    "..1111111111....",
    ".12244444421....",
    ".12244444421....",
    ".12222222221....",
    "11111111111111..",
    "12222222222221..",
    "12233222233221..",
    "11111111111111..",
    "..1.5.....5.1...",
    "..15551.15551...",
    "..15551.15551...",
    "...151...151....",
    "................",
    "................",
])

# --- Poachermon: elephant -------------------------------------------------
ELEPHANT = art([
    "................",
    "...22......22...",
    "..3223....3223..",
    "..32222222223...",
    "..3222222222 3.."[:16],
    "..322122122 23.."[:16],
    "..3222222222 3.."[:16],
    "..32222222223...",
    "...322222223....",
    "...3222.2223....",
    "...32.2.2.23....",
    "...3.2.2.2.3....",
    "...11.....11....",
    "................",
    "................",
    "................",
])

# --- Poachermon: rhino ----------------------------------------------------
RHINO = art([
    "................",
    "............4...",
    "...........441..",
    "..2222....4221..",
    ".222222222221...",
    ".2212222222221..",
    ".222222222222...",
    ".22222222222....",
    ".2222222222.....",
    ".22.2222.22.....",
    ".2.2.22.2.2.....",
    ".1.1.11.1.1.....",
    "................",
    "................",
    "................",
    "................",
])

# --- Poachermon: lion cub -------------------------------------------------
LIONCUB = art([
    "................",
    "....4....4......",
    "...434..434.....",
    "..43333333334...",
    "..4332222233 4.."[:16],
    "..433212123334.."[:16],
    "..43322222234...",
    "..43322422234...",
    "...433333334....",
    "....3222223.....",
    "...32222222 3...",
    "...3222222223...",
    "...3.22..22.3...",
    "...1.1....1.1...",
    "................",
    "................",
])

# --- Poachermon: bird -----------------------------------------------------
BIRD = art([
    "................",
    "................",
    ".......11.......",
    "......1221......",
    ".....122221.....",
    "....13222231....",
    "...1322222231...",
    "..132222222231..",
    "..13222222 2231."[:16],
    "...1322222231...",
    "....14222241....",
    ".....144441.....",
    "......1441......",
    ".......11.......",
    "................",
    "................",
])


def sprite(sid, name, palette, frames):
    return {
        "id": sid, "name": name, "width": 16, "height": 16, "palette": palette,
        "frames": [{"id": f"{sid}_{i}", "name": f"Frame {i}", "pixels": px}
                   for i, px in enumerate(frames)],
    }


def main() -> None:
    project = {
        "schema_version": "1.0",
        "name": "Poachermon",
        "target": "snes",
        "rom": {"title": "POACHERMON", "region": "NTSC"},
        "learner": {
            "age_band": "kids",
            "require_human_review": True,
            "mentor_notes": [
                "Poachermon teaches conservation with humour: rangers protect wild creatures.",
                "Gotta Save 'Em All — rescue the elephant, rhino, lion cub and bird.",
                "Review every helper patch before applying it.",
            ],
        },
        "flags": {"found_poacher": False, "poacher_caught": False, "camera_set": False},
        "variables": {"rescued": 0, "score": 0},
        "sprites": [
            sprite("ranger", "Park Ranger (You)",
                   ["#000000", "#15151a", "#f1c08a", "#6b3f1d", "#3f6e2e", "#cdb78d"],
                   [RANGER]),
            sprite("poacher", "Poacher",
                   ["#000000", "#15151a", "#f1c08a", "#9b2c2c", "#4b5563", "#6b3f1d"],
                   [POACHER]),
            sprite("jeep", "Poacher's Jeep",
                   ["#000000", "#14210f", "#3f6e2e", "#24401a", "#e6dcae", "#1c1c1c"],
                   [JEEP]),
            sprite("elephant", "Elephant",
                   ["#000000", "#4b5563", "#9aa0a6", "#cdd2d8"],
                   [ELEPHANT]),
            sprite("rhino", "Rhino",
                   ["#000000", "#4b5563", "#8b9298", "#c2c7cd", "#ece6d2"],
                   [RHINO]),
            sprite("lioncub", "Lion Cub",
                   ["#000000", "#7a3b12", "#d98a3d", "#f0c489", "#4a2a0e"],
                   [LIONCUB]),
            sprite("bird", "Bird",
                   ["#000000", "#1a1a1a", "#f5c518", "#e07b2a", "#d94f2a"],
                   [BIRD]),
        ],
        "assets": [
            {"id": "title_bg", "name": "Title Screen", "type": "background", "path": "assets/backgrounds/title.png"},
            {"id": "station_bg", "name": "Ranger Station", "type": "background", "path": "assets/backgrounds/station.png"},
            {"id": "savannah_bg", "name": "Savannah Map", "type": "background", "path": "assets/backgrounds/savannah.png"},
            {"id": "chase_bg", "name": "Chase Road", "type": "background", "path": "assets/backgrounds/chase.png"},
            {"id": "rescue_bg", "name": "Rescue Clearing", "type": "background", "path": "assets/backgrounds/rescue.png"},
            {"id": "alert", "name": "Alert", "type": "sound", "path": "assets/sounds/alert.wav"},
        ],
        "scenes": [
            {
                "id": "title", "name": "Title Screen", "background": "title_bg",
                "actors": [
                    {"id": "title_ranger", "name": "Ranger", "x": 88, "y": 150, "sprite": "ranger", "events": {}},
                    {"id": "title_elephant", "name": "Elephant", "x": 150, "y": 144, "sprite": "elephant", "events": {}},
                    {"id": "title_bird", "name": "Bird", "x": 60, "y": 56, "sprite": "bird", "events": {}},
                ],
                "collision": [],
                "triggers": [
                    {"id": "press_start", "name": "Press Start", "x": 0, "y": 0, "w": 256, "h": 224, "event": "start_game"},
                ],
            },
            {
                "id": "station", "name": "Ranger Station", "background": "station_bg",
                "actors": [
                    {"id": "ranger", "name": "Ranger (You)", "x": 40, "y": 120, "sprite": "ranger", "events": {}},
                    {"id": "tulip", "name": "Professor Tulip", "x": 150, "y": 110, "sprite": "ranger", "events": {"interact": "briefing"}},
                ],
                "collision": [
                    {"id": "desk", "x": 120, "y": 130, "w": 64, "h": 24},
                    {"id": "wall", "x": 0, "y": 0, "w": 256, "h": 24},
                ],
                "triggers": [
                    {"id": "to_savannah", "name": "Out to the reserve", "x": 232, "y": 96, "w": 24, "h": 48, "event": "head_out"},
                ],
            },
            {
                "id": "savannah", "name": "Savannah Map", "background": "savannah_bg",
                "actors": [
                    {"id": "ranger_s", "name": "Ranger (You)", "x": 32, "y": 120, "sprite": "ranger", "events": {}},
                    {"id": "elephant", "name": "Elephant", "x": 96, "y": 72, "sprite": "elephant", "events": {"interact": "talk_elephant"}},
                    {"id": "rhino", "name": "Rhino", "x": 168, "y": 150, "sprite": "rhino", "events": {"interact": "talk_rhino"}},
                    {"id": "lioncub", "name": "Lion Cub", "x": 72, "y": 168, "sprite": "lioncub", "events": {"interact": "talk_lioncub"}},
                    {"id": "bird", "name": "Bird", "x": 200, "y": 56, "sprite": "bird", "events": {"interact": "talk_bird"}},
                    {"id": "poacher_s", "name": "Sneaky Poacher", "x": 210, "y": 120, "sprite": "poacher", "events": {"interact": "meet_poacher"}},
                ],
                "collision": [
                    {"id": "rock", "x": 120, "y": 40, "w": 24, "h": 24},
                    {"id": "waterhole", "x": 150, "y": 176, "w": 56, "h": 24},
                ],
                "triggers": [
                    {"id": "poacher_zone", "name": "Poacher Ambush", "x": 190, "y": 104, "w": 48, "h": 48, "event": "meet_poacher"},
                ],
            },
            {
                "id": "chase", "name": "Chase Road", "background": "chase_bg",
                "actors": [
                    {"id": "ranger_c", "name": "Ranger (You)", "x": 24, "y": 150, "sprite": "ranger", "events": {}},
                    {"id": "getaway_jeep", "name": "Poacher's Jeep", "x": 190, "y": 96, "sprite": "jeep", "events": {"interact": "chase_quip"}},
                ],
                "collision": [],
                "triggers": [],
            },
            {
                "id": "rescue", "name": "Rescue Clearing", "background": "rescue_bg",
                "actors": [
                    {"id": "ranger_r", "name": "Ranger (You)", "x": 40, "y": 150, "sprite": "ranger", "events": {}},
                    {"id": "poacher_r", "name": "Cornered Poacher", "x": 200, "y": 90, "sprite": "poacher", "events": {"interact": "confiscate"}},
                    {"id": "saved_one", "name": "Rescued Elephant", "x": 120, "y": 150, "sprite": "elephant", "events": {"interact": "thank_you"}},
                ],
                "collision": [],
                "triggers": [],
            },
        ],
        "eventChains": [
            {"id": "title_intro", "name": "Title Screen", "trigger": {"type": "scene_start", "scene": "title"}, "steps": [
                {"id": "ti_1", "type": "show_text", "text": "* POACHERMON *"},
                {"id": "ti_2", "type": "show_text", "text": "Gotta Save 'Em All!"},
                {"id": "ti_3", "type": "show_text", "text": "A park ranger vs. one very rude poacher."},
                {"id": "ti_4", "type": "show_text", "text": "Press A to begin your patrol."},
            ]},
            {"id": "start_game", "name": "Start the Game", "trigger": {"type": "zone_enter", "zone": "press_start"}, "steps": [
                {"id": "sg_go", "type": "change_scene", "scene": "station"},
            ]},
            {"id": "briefing", "name": "Professor Tulip's Briefing", "trigger": {"type": "actor_interact", "actor": "tulip"}, "steps": [
                {"id": "br_1", "type": "show_text", "text": "Prof. Tulip: Set camera traps. Try to look heroic."},
                {"id": "br_set", "type": "set_flag", "flag": "camera_set", "value": True},
                {"id": "br_2", "type": "show_text", "text": "Ranger: Another fine day to chase poor decisions."},
            ]},
            {"id": "head_out", "name": "Head to the Reserve", "trigger": {"type": "zone_enter", "zone": "to_savannah"}, "steps": [
                {"id": "ho_go", "type": "change_scene", "scene": "savannah"},
            ]},
            {"id": "savannah_intro", "name": "Arrive in the Savannah", "trigger": {"type": "scene_start", "scene": "savannah"}, "steps": [
                {"id": "si_check", "type": "if_flag", "flag": "camera_set",
                 "then": [{"id": "si_yes", "type": "show_text", "text": "The reserve is quiet... too quiet. Find the creatures and the poacher."}],
                 "else": [{"id": "si_no", "type": "show_text", "text": "You forgot the camera traps, but onward!"}]},
            ]},
            {"id": "talk_elephant", "name": "Talk to Elephant", "trigger": {"type": "actor_interact", "actor": "elephant"}, "steps": [
                {"id": "te_1", "type": "show_text", "text": "Elephant: We rely on you, Ranger."},
            ]},
            {"id": "talk_bird", "name": "Talk to Bird", "trigger": {"type": "actor_interact", "actor": "bird"}, "steps": [
                {"id": "tb_1", "type": "show_text", "text": "Bird: Camera here? Fine, but I expect royalties."},
            ]},
            {"id": "talk_rhino", "name": "Talk to Rhino", "trigger": {"type": "actor_interact", "actor": "rhino"}, "steps": [
                {"id": "tr_1", "type": "show_text", "text": "Rhino snorts. (Roughly: 'hurry up.')"},
            ]},
            {"id": "talk_lioncub", "name": "Talk to Lion Cub", "trigger": {"type": "actor_interact", "actor": "lioncub"}, "steps": [
                {"id": "tl_1", "type": "show_text", "text": "Lion cub mews. Gotta save 'em all!"},
            ]},
            {"id": "meet_poacher", "name": "Confront the Poacher", "trigger": {"type": "actor_interact", "actor": "poacher_s"}, "steps": [
                {"id": "mp_flag", "type": "set_flag", "flag": "found_poacher", "value": True},
                {"id": "mp_say", "type": "show_text", "text": "Poacher: These creatures are MINE, ranger!"},
                {"id": "mp_quip", "type": "show_text", "text": "Ranger: Pull over before I quote Stobbart."},
                {"id": "mp_go", "type": "change_scene", "scene": "chase"},
            ]},
            {"id": "chase_intro", "name": "The Chase Begins", "trigger": {"type": "scene_start", "scene": "chase"}, "steps": [
                {"id": "ci_check", "type": "if_flag", "flag": "found_poacher",
                 "then": [{"id": "ci_yes", "type": "show_text", "text": "Floor it! Catch the jeep before it escapes."}],
                 "else": [{"id": "ci_no", "type": "show_text", "text": "A wild getaway begins!"}]},
            ]},
            {"id": "chase_quip", "name": "Run Down the Jeep", "trigger": {"type": "actor_interact", "actor": "getaway_jeep"}, "steps": [
                {"id": "cq_1", "type": "show_text", "text": "Ranger: You call that a getaway?"},
                {"id": "cq_2", "type": "show_text", "text": "Poacher: Not the Broken Sword speeches!"},
                {"id": "cq_go", "type": "change_scene", "scene": "rescue"},
            ]},
            {"id": "rescue_intro", "name": "Cornered at Last", "trigger": {"type": "scene_start", "scene": "rescue"}, "steps": [
                {"id": "ri_1", "type": "show_text", "text": "You cornered the poacher. Talk to them to confiscate the snare."},
            ]},
            {"id": "confiscate", "name": "Confiscate the Snare", "trigger": {"type": "actor_interact", "actor": "poacher_r"}, "steps": [
                {"id": "cf_1", "type": "show_text", "text": "Ranger: Another snare off the map."},
                {"id": "cf_flag", "type": "set_flag", "flag": "poacher_caught", "value": True},
                {"id": "cf_score", "type": "set_variable", "variable": "rescued", "value": 1},
                {"id": "cf_2", "type": "show_text", "text": "The poacher flees. You saved a Poachermon!"},
                {"id": "cf_3", "type": "show_text", "text": "Prof. Tulip: The press calls you 'The Throttle of Justice.'"},
            ]},
            {"id": "thank_you", "name": "A Grateful Creature", "trigger": {"type": "actor_interact", "actor": "saved_one"}, "steps": [
                {"id": "ty_1", "type": "show_text", "text": "Elephant: Peace returns to the reserve. Thank you, Ranger."},
            ]},
        ],
    }

    # Validate against the real schema before writing.
    validated = model_to_jsonable(Project.model_validate(project))

    out_main = ROOT / "examples" / "poachermon" / "project.snesproj"
    out_web = ROOT / "web" / "public" / "examples" / "poachermon.snesproj"
    out_main.parent.mkdir(parents=True, exist_ok=True)
    out_web.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(validated, indent=2) + "\n"
    out_main.write_text(text, encoding="utf-8")
    out_web.write_text(text, encoding="utf-8")
    print(f"Wrote {out_main}")
    print(f"Wrote {out_web}")
    print(f"Sprites: {[s['id'] for s in validated['sprites']]}")
    print(f"Scenes: {[s['id'] for s in validated['scenes']]}")
    print(f"Chains: {[c['id'] for c in validated['eventChains']]}")


if __name__ == "__main__":
    main()
