"""Generate Mango Island, an original pirate-adventure demake project.

The game is inspired by classic comedic point-and-click pacing: talk, inspect,
collect clues, move between compact scenes. It avoids copied names, dialogue,
and assets from commercial adventures.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from snesstudio.schema import Project, model_to_jsonable  # noqa: E402


def art(rows: list[str]) -> list[int]:
    assert len(rows) == 16
    pixels: list[int] = []
    for row in rows:
        assert len(row) == 16, row
        pixels.extend(0 if ch in ". " else int(ch, 16) for ch in row)
    return pixels


PIRATE = art([
    "................",
    ".....11111......",
    "....1222221.....",
    "....2333332.....",
    "....2323232.....",
    "....2333332.....",
    ".....3333.......",
    "....444444......",
    "...54444445.....",
    "...54444445.....",
    "....444444......",
    "....666666......",
    "....66..66......",
    "....66..66......",
    "....77..77......",
    "................",
])

CAPTAIN = art([
    "................",
    "....111111......",
    "...12222221.....",
    "...23333332.....",
    "...23233232.....",
    "...23333332.....",
    "....333333......",
    "...44444444.....",
    "..5444444445....",
    "..5444444445....",
    "...44444444.....",
    "...66666666.....",
    "...66....66.....",
    "...66....66.....",
    "...77....77.....",
    "................",
])

BARKEEP = art([
    "................",
    ".....1111.......",
    "....122221......",
    "....233332......",
    "....232232......",
    "....233332......",
    ".....3333.......",
    "....555555......",
    "...55555555.....",
    "...54455445.....",
    "....555555......",
    "....666666......",
    "....66..66......",
    "....66..66......",
    "....77..77......",
    "................",
])

MONKEY = art([
    "................",
    "................",
    "......11........",
    ".....1221.......",
    "....123321......",
    "....132231......",
    "....123321......",
    ".....1221.......",
    "...44111144.....",
    "..4441111444....",
    "..44.1111.44....",
    ".....1..1.......",
    "....11..11......",
    "...11....11.....",
    "................",
    "................",
])

CHEST = art([
    "................",
    "................",
    "...11111111.....",
    "..122222221.....",
    ".12222222221....",
    ".11111111111....",
    ".13333333331....",
    ".13333433331....",
    ".13333333331....",
    ".11111111111....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
])


def sprite(sid: str, name: str, palette: list[str], pixels: list[int]) -> dict:
    return {
        "id": sid,
        "name": name,
        "width": 16,
        "height": 16,
        "palette": palette,
        "frames": [{"id": "idle_0", "name": "Idle", "pixels": pixels}],
    }


def zone(zid: str, name: str, x: int, y: int, w: int, h: int, event: str) -> dict:
    return {"id": zid, "name": name, "x": x, "y": y, "w": w, "h": h, "event": event}


def text_step(sid: str, text: str) -> dict:
    return {"id": sid, "type": "show_text", "text": text}


def main() -> None:
    project = {
        "schema_version": "1.0",
        "name": "Mango Island",
        "target": "snes",
        "rom": {"title": "MANGO ISLAND", "region": "NTSC"},
        "learner": {
            "age_band": "kids",
            "require_human_review": True,
            "mentor_notes": ["Original pirate adventure demake for SNES Studio."],
        },
        "flags": {"map_piece": False, "got_mug": False, "opened_gate": False, "treasure_found": False},
        "variables": {"score": 0},
        "sprites": [
            sprite("rookie", "Rookie Pirate", ["#000000", "#5b2d16", "#f0c48a", "#2b1d14", "#d94b72", "#ffffff", "#314c8f", "#33281f"], PIRATE),
            sprite("captain", "Captain Brine", ["#000000", "#34251f", "#f0c48a", "#ffffff", "#4f8bff", "#f2c34f", "#4b465d", "#211d2c"], CAPTAIN),
            sprite("barkeep", "Barkeep", ["#000000", "#5b2d16", "#f0c48a", "#211d2c", "#ffffff", "#38a86f", "#314c8f", "#33281f"], BARKEEP),
            sprite("monkey", "Harbor Monkey", ["#000000", "#5b2d16", "#f0c48a", "#ffffff", "#7a4a20"], MONKEY),
            sprite("chest", "Treasure Chest", ["#000000", "#5b2d16", "#f2c34f", "#7a4a20", "#ffffff"], CHEST),
        ],
        "assets": [
            {"id": "dock_bg", "name": "Moonlit Dock", "type": "background"},
            {"id": "tavern_bg", "name": "Tavern", "type": "background"},
            {"id": "jungle_bg", "name": "Mango Jungle", "type": "background"},
            {"id": "cave_bg", "name": "Cave Door", "type": "background"},
            {"id": "vault_bg", "name": "Vault", "type": "background"},
        ],
        "scenes": [
            {
                "id": "dock",
                "name": "Moonlit Dock",
                "background": "dock_bg",
                "actors": [
                    {"id": "hero_dock", "name": "Rookie Pirate", "x": 36, "y": 136, "sprite": "rookie", "events": {}},
                    {"id": "captain_dock", "name": "Captain Brine", "x": 178, "y": 112, "sprite": "captain", "events": {"interact": "talk_captain"}},
                    {"id": "monkey_dock", "name": "Tiny Lookout", "x": 106, "y": 70, "sprite": "monkey", "events": {"interact": "talk_monkey"}},
                ],
                "collision": [{"id": "pier_posts", "x": 88, "y": 160, "w": 72, "h": 16}],
                "triggers": [zone("dock_to_tavern", "Tavern Door", 224, 104, 24, 48, "go_tavern")],
            },
            {
                "id": "tavern",
                "name": "The Bent Compass",
                "background": "tavern_bg",
                "actors": [
                    {"id": "hero_tavern", "name": "Rookie Pirate", "x": 40, "y": 138, "sprite": "rookie", "events": {}},
                    {"id": "barkeep", "name": "Barkeep", "x": 146, "y": 112, "sprite": "barkeep", "events": {"interact": "talk_barkeep"}},
                ],
                "collision": [{"id": "bar", "x": 112, "y": 130, "w": 88, "h": 18}],
                "triggers": [zone("tavern_to_jungle", "Back Alley", 224, 132, 24, 48, "go_jungle")],
            },
            {
                "id": "jungle",
                "name": "Mango Jungle",
                "background": "jungle_bg",
                "actors": [
                    {"id": "hero_jungle", "name": "Rookie Pirate", "x": 36, "y": 132, "sprite": "rookie", "events": {}},
                    {"id": "monkey_jungle", "name": "Tiny Lookout", "x": 152, "y": 88, "sprite": "monkey", "events": {"interact": "trade_monkey"}},
                ],
                "collision": [{"id": "vines", "x": 88, "y": 46, "w": 24, "h": 82}],
                "triggers": [zone("jungle_to_cave", "Old Stone Path", 224, 84, 24, 58, "go_cave")],
            },
            {
                "id": "cave",
                "name": "Cave Door",
                "background": "cave_bg",
                "actors": [
                    {"id": "hero_cave", "name": "Rookie Pirate", "x": 40, "y": 132, "sprite": "rookie", "events": {}},
                    {"id": "captain_cave", "name": "Captain Brine", "x": 150, "y": 104, "sprite": "captain", "events": {"interact": "open_cave"}},
                ],
                "collision": [{"id": "stone_door", "x": 180, "y": 70, "w": 42, "h": 80}],
                "triggers": [zone("cave_to_vault", "Hidden Opening", 218, 96, 30, 48, "enter_vault")],
            },
            {
                "id": "vault",
                "name": "Captain Lime's Vault",
                "background": "vault_bg",
                "actors": [
                    {"id": "hero_vault", "name": "Rookie Pirate", "x": 44, "y": 132, "sprite": "rookie", "events": {}},
                    {"id": "treasure", "name": "Mango Chest", "x": 162, "y": 112, "sprite": "chest", "events": {"interact": "open_chest"}},
                ],
                "collision": [],
                "triggers": [],
            },
        ],
        "eventChains": [
            {"id": "dock_intro", "name": "Dock Intro", "trigger": {"type": "scene_start", "scene": "dock"}, "steps": [
                text_step("di1", "Mango Island: a tiny pirate tale."),
                text_step("di2", "Find a map, win a mug, bribe a lookout, open the vault."),
            ]},
            {"id": "talk_captain", "name": "Talk Captain", "trigger": {"type": "actor_interact", "actor": "captain_dock"}, "steps": [
                text_step("tc1", "Captain Brine: Treasure hunting starts with paperwork."),
                text_step("tc2", "Try the tavern. Someone always lost a map there."),
            ]},
            {"id": "talk_monkey", "name": "Talk Lookout", "trigger": {"type": "actor_interact", "actor": "monkey_dock"}, "steps": [
                text_step("tm1", "Tiny Lookout: No mug, no cave gossip."),
            ]},
            {"id": "go_tavern", "name": "Go Tavern", "trigger": {"type": "zone_enter", "zone": "dock_to_tavern"}, "steps": [{"id": "gt", "type": "change_scene", "scene": "tavern"}]},
            {"id": "tavern_intro", "name": "Tavern Intro", "trigger": {"type": "scene_start", "scene": "tavern"}, "steps": [
                text_step("ti1", "The Bent Compass smells like salt, smoke, and bad wagers."),
            ]},
            {"id": "talk_barkeep", "name": "Talk Barkeep", "trigger": {"type": "actor_interact", "actor": "barkeep"}, "steps": [
                text_step("tb1", "Barkeep: A map piece for a joke? Fine. Make it short."),
                text_step("tb2", "Rookie: Why did the pirate alphabet stop at R?"),
                text_step("tb3", "Barkeep: Because the sea took the rest. Terrible. Take it."),
                {"id": "tb_flag", "type": "set_flag", "flag": "map_piece", "value": True},
                {"id": "tb_mug", "type": "set_flag", "flag": "got_mug", "value": True},
                text_step("tb4", "You got a cracked mug and a damp map piece."),
            ]},
            {"id": "go_jungle", "name": "Go Jungle", "trigger": {"type": "zone_enter", "zone": "tavern_to_jungle"}, "steps": [{"id": "gj", "type": "change_scene", "scene": "jungle"}]},
            {"id": "trade_monkey", "name": "Trade Lookout", "trigger": {"type": "actor_interact", "actor": "monkey_jungle"}, "steps": [
                {"id": "tr_check", "type": "if_flag", "flag": "got_mug",
                 "then": [text_step("tr_yes", "Tiny Lookout: A mug! Cave password is 'soggy mango'."), {"id": "tr_gate", "type": "set_flag", "flag": "opened_gate", "value": True}],
                 "else": [text_step("tr_no", "Tiny Lookout: Bring me tavern treasure first. Preferably ceramic.")]},
            ]},
            {"id": "go_cave", "name": "Go Cave", "trigger": {"type": "zone_enter", "zone": "jungle_to_cave"}, "steps": [{"id": "gc", "type": "change_scene", "scene": "cave"}]},
            {"id": "open_cave", "name": "Open Cave", "trigger": {"type": "actor_interact", "actor": "captain_cave"}, "steps": [
                {"id": "oc_check", "type": "if_flag", "flag": "opened_gate",
                 "then": [text_step("oc_yes", "Captain Brine: Soggy mango? Correct. The door sulks open.")],
                 "else": [text_step("oc_no", "Captain Brine: The door wants a password and better manners.")]},
            ]},
            {"id": "enter_vault", "name": "Enter Vault", "trigger": {"type": "zone_enter", "zone": "cave_to_vault"}, "steps": [
                {"id": "ev_check", "type": "if_flag", "flag": "opened_gate",
                 "then": [{"id": "ev_go", "type": "change_scene", "scene": "vault"}],
                 "else": [text_step("ev_no", "The stone door refuses to move.")]},
            ]},
            {"id": "open_chest", "name": "Open Chest", "trigger": {"type": "actor_interact", "actor": "treasure"}, "steps": [
                text_step("ch1", "The chest opens with a heroic creak."),
                text_step("ch2", "Inside: one golden mango and a note saying 'Share nicely.'"),
                {"id": "ch_flag", "type": "set_flag", "flag": "treasure_found", "value": True},
                {"id": "ch_score", "type": "set_variable", "variable": "score", "value": 100},
            ]},
        ],
    }

    validated = model_to_jsonable(Project.model_validate(project))
    out_main = ROOT / "examples" / "mango-island" / "project.snesproj"
    out_web = ROOT / "web" / "public" / "examples" / "mango-island.snesproj"
    out_main.parent.mkdir(parents=True, exist_ok=True)
    out_web.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(validated, indent=2) + "\n"
    out_main.write_text(text, encoding="utf-8")
    out_web.write_text(text, encoding="utf-8")
    print(f"Wrote {out_main}")
    print(f"Wrote {out_web}")


if __name__ == "__main__":
    main()
