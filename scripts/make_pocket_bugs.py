"""Generate the Pocket Bugs demo project.

Pocket Bugs is an original creature-battler RPG demo:
- kids catch bugs in a backyard
- bugs are carried in small matchboxes
- kids battle those bugs in a club tournament
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from snesstudio.schema import Project, model_to_jsonable  # noqa: E402

W = 32
H = 28


def art(rows: list[str]) -> list[int]:
    """Parse 16x16 sprite art. '.' and ' ' map to palette index 0."""
    if len(rows) != 16:
        raise ValueError(f"expected 16 rows, got {len(rows)}")
    out: list[int] = []
    for row in rows:
        if len(row) != 16:
            raise ValueError(f"expected 16 columns, got {len(row)}: {row!r}")
        for ch in row:
            out.append(0 if ch in ". " else int(ch, 16))
    return out


def sprite(sprite_id: str, name: str, palette: list[str], frames: list[list[int]]) -> dict:
    return {
        "id": sprite_id,
        "name": name,
        "width": 16,
        "height": 16,
        "palette": palette,
        "frames": [
            {"id": f"{sprite_id}_{i}", "name": f"Frame {i}", "pixels": frame}
            for i, frame in enumerate(frames)
        ],
    }


def flat(color: int) -> list[int]:
    return [color] * (W * H)


def paint_rect(p: list[int], x: int, y: int, w: int, h: int, color: int) -> None:
    for yy in range(y, min(y + h, H)):
        for xx in range(x, min(x + w, W)):
            p[yy * W + xx] = color


def bordered(fill: int, edge: int) -> list[int]:
    p = flat(fill)
    for x in range(W):
        p[x] = edge
        p[(H - 1) * W + x] = edge
    for y in range(H):
        p[y * W] = edge
        p[y * W + (W - 1)] = edge
    return p


KID_0 = art([
    "................",
    ".....1111.......",
    "....122221......",
    "....123321......",
    "....122221......",
    ".....1221.......",
    "....444444......",
    "...54444445.....",
    "...54444445.....",
    "...54444445.....",
    "....445544......",
    "....445544......",
    "....555555......",
    "....55..55......",
    "....55..55......",
    "....33..33......",
])

KID_1 = art([
    "................",
    ".....1111.......",
    "....122221......",
    "....123321......",
    "....122221......",
    ".....1221.......",
    "....444444......",
    "...54444445.....",
    "...54444445.....",
    "...54444445.....",
    "....445544......",
    "....455544......",
    "....555555......",
    "....55..55......",
    "....55..55......",
    "....33..33......",
])

RIVAL = art([
    "................",
    ".....1111.......",
    "....133331......",
    "....134431......",
    "....133331......",
    ".....1331.......",
    "....444444......",
    "...64444446.....",
    "...64444446.....",
    "...64444446.....",
    "....446644......",
    "....446644......",
    "....666666......",
    "....66..66......",
    "....66..66......",
    "....33..33......",
])

JUDGE = art([
    "................",
    ".....1111.......",
    "....122221......",
    "....123321......",
    "....122221......",
    ".....1221.......",
    "....666666......",
    "...56666665.....",
    "...56666665.....",
    "...56666665.....",
    "....665566......",
    "....665566......",
    "....555555......",
    "....55..55......",
    "....55..55......",
    "....33..33......",
])

MATCHBOX = art([
    "................",
    "................",
    "...1111111111...",
    "..122222222221..",
    ".12333333333321.",
    ".12344444444321.",
    ".12344444444321.",
    ".12345555554321.",
    ".12345555554321.",
    ".12344444444321.",
    ".12344444444321.",
    ".12333333333321.",
    "..122222222221..",
    "...1111111111...",
    "................",
    "................",
])

LADYBYTE_0 = art([
    "................",
    "................",
    "......1111......",
    ".....122221.....",
    "....12333321....",
    "...1234444321...",
    "...1234444321...",
    "...1234554321...",
    "...1234554321...",
    "...1234444321...",
    "....12333321....",
    ".....122221.....",
    "......1111......",
    "................",
    "................",
    "................",
])

LADYBYTE_1 = art([
    "................",
    "................",
    "......1111......",
    ".....122221.....",
    "....12333321....",
    "...1234545321...",
    "...1234444321...",
    "...1234554321...",
    "...1234554321...",
    "...1234444321...",
    "....12333321....",
    ".....122221.....",
    "......1111......",
    "................",
    "................",
    "................",
])

BEETITAN_0 = art([
    "................",
    ".......11.......",
    "......1221......",
    ".....123321.....",
    "....12344321....",
    "...1234444321...",
    "...1234554321...",
    "...1234554321...",
    "...1234554321...",
    "...1234444321...",
    "....12344321....",
    ".....122221.....",
    "....11....11....",
    "...11......11...",
    "................",
    "................",
])

BEETITAN_1 = art([
    "................",
    ".......11.......",
    "......1221......",
    ".....123321.....",
    "....12344321....",
    "...1234444321...",
    "...1234564321...",
    "...1234554321...",
    "...1234564321...",
    "...1234444321...",
    "....12344321....",
    ".....122221.....",
    "...111....111...",
    "..11........11..",
    "................",
    "................",
])

MANTYKID_0 = art([
    "................",
    ".....11..11.....",
    "....12211221....",
    "....12222221....",
    ".....123321.....",
    "....12344321....",
    "...1234554321...",
    "....12344321....",
    ".....123321.....",
    "....11222211....",
    "...11..22..11...",
    "..11...22...11..",
    "................",
    "................",
    "................",
    "................",
])

MANTYKID_1 = art([
    "................",
    "....11....11....",
    "...1221..1221...",
    "....12222221....",
    ".....123321.....",
    "....12344321....",
    "...1234554321...",
    "....12344321....",
    ".....123321.....",
    "...1112222111...",
    "..11...22...11..",
    ".11....22....11.",
    "................",
    "................",
    "................",
    "................",
])


def scene_title() -> list[int]:
    p = flat(1)
    paint_rect(p, 0, 10, W, 18, 2)
    paint_rect(p, 10, 10, 12, 18, 3)
    paint_rect(p, 11, 11, 10, 16, 4)
    return p


def scene_garden() -> list[int]:
    p = bordered(2, 4)
    paint_rect(p, 14, 0, 4, H, 3)
    paint_rect(p, 0, 12, W, 4, 3)
    paint_rect(p, 4, 4, 6, 6, 5)
    paint_rect(p, 22, 18, 6, 6, 5)
    return p


def scene_patch() -> list[int]:
    p = bordered(2, 4)
    paint_rect(p, 8, 9, 16, 10, 5)
    paint_rect(p, 11, 11, 10, 6, 6)
    return p


def scene_club() -> list[int]:
    p = bordered(1, 6)
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            p[y * W + x] = 2 if (x + y) % 2 == 0 else 3
    paint_rect(p, 10, 8, 12, 12, 5)
    paint_rect(p, 11, 9, 10, 10, 4)
    return p


def scene_battle(fill: int, ring: int, edge: int) -> list[int]:
    p = bordered(fill, edge)
    paint_rect(p, 8, 7, 16, 14, ring)
    paint_rect(p, 9, 8, 14, 12, fill)
    paint_rect(p, 11, 10, 10, 8, ring)
    return p


def build_project() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Pocket Bugs",
        "target": "snes",
        "rom": {"title": "POCKET BUGS", "region": "NTSC"},
        "learner": {
            "age_band": "kids",
            "require_human_review": True,
            "mentor_notes": [
                "Original monster-battler style game with bugs and matchboxes.",
                "Catch bugs in the garden and battle in the Backyard Bug Club.",
                "Battle scenes are scripted event chains for ROM/runtime parity.",
            ],
        },
        "flags": {
            "has_bug": False,
            "caught_ladybyte": False,
            "caught_beetitan": False,
            "registered_for_cup": False,
            "won_round_one": False,
            "won_round_two": False,
        },
        "variables": {"bugs_found": 0, "wins": 0},
        "sprites": [
            sprite("kid_player", "You (Bug Tamer)",
                   ["#000000", "#2a2a2a", "#f1c08a", "#1f3a8a", "#7c3aed", "#22c55e"],
                   [KID_0, KID_1]),
            sprite("kid_rival", "Rival Kid",
                   ["#000000", "#2a2a2a", "#f1c08a", "#b91c1c", "#1d4ed8", "#0f766e", "#f59e0b"],
                   [RIVAL]),
            sprite("kid_judge", "Club Judge",
                   ["#000000", "#1f2937", "#f1c08a", "#0f172a", "#334155", "#6d28d9", "#a3a3a3"],
                   [JUDGE]),
            sprite("matchbox", "Matchbox",
                   ["#000000", "#7c2d12", "#dc2626", "#fde68a", "#fef3c7"],
                   [MATCHBOX]),
            sprite("ladybyte", "LadyByte",
                   ["#000000", "#7f1d1d", "#b91c1c", "#ef4444", "#111827", "#f59e0b"],
                   [LADYBYTE_0, LADYBYTE_1]),
            sprite("beetitan", "Beetitan",
                   ["#000000", "#1f2937", "#4338ca", "#6366f1", "#a5b4fc", "#c4b5fd", "#facc15"],
                   [BEETITAN_0, BEETITAN_1]),
            sprite("mantykid", "Mantykid",
                   ["#000000", "#14532d", "#16a34a", "#4ade80", "#86efac", "#fef08a"],
                   [MANTYKID_0, MANTYKID_1]),
        ],
        "assets": [
            {"id": "title_bg", "name": "Title", "type": "background", "path": "assets/backgrounds/pocketbugs_title.png"},
            {"id": "garden_bg", "name": "Garden", "type": "background", "path": "assets/backgrounds/pocketbugs_garden.png"},
            {"id": "patch_bg", "name": "Patch", "type": "background", "path": "assets/backgrounds/pocketbugs_patch.png"},
            {"id": "club_bg", "name": "Club", "type": "background", "path": "assets/backgrounds/pocketbugs_club.png"},
            {"id": "arena1_bg", "name": "Arena One", "type": "background", "path": "assets/backgrounds/pocketbugs_arena1.png"},
            {"id": "arena2_bg", "name": "Arena Two", "type": "background", "path": "assets/backgrounds/pocketbugs_arena2.png"},
            {"id": "buzz", "name": "Buzz", "type": "sound", "path": "assets/sounds/buzz.wav"},
            {"id": "thump", "name": "Thump", "type": "sound", "path": "assets/sounds/thump.wav"},
        ],
        "scenes": [
            {
                "id": "title",
                "name": "Pocket Bugs Title",
                "background": "title_bg",
                "paint_palette": ["#4c1d95", "#312e81", "#166534", "#65a30d", "#facc15", "#ffffff"],
                "paint": scene_title(),
                "actors": [
                    {"id": "title_hero", "name": "Bug Tamer", "x": 84, "y": 152, "sprite": "kid_player", "events": {}},
                    {"id": "title_bug", "name": "LadyByte", "x": 150, "y": 146, "sprite": "ladybyte", "events": {}},
                    {"id": "title_box", "name": "Matchbox", "x": 56, "y": 154, "sprite": "matchbox", "events": {}},
                ],
                "collision": [],
                "triggers": [
                    {"id": "press_start", "name": "Press Start", "x": 0, "y": 0, "w": 256, "h": 224, "event": "start_adventure"},
                ],
            },
            {
                "id": "garden_hub",
                "name": "Backyard Garden",
                "background": "garden_bg",
                "paint_palette": ["#14532d", "#166534", "#22c55e", "#ca8a04", "#713f12", "#fef08a", "#a78bfa"],
                "paint": scene_garden(),
                "actors": [
                    {"id": "player_hub", "name": "You", "x": 120, "y": 112, "sprite": "kid_player", "events": {}},
                    {"id": "judge_hub", "name": "Club Judge", "x": 215, "y": 120, "sprite": "kid_judge", "events": {"interact": "judge_hub_hint"}},
                    {"id": "rival_hub", "name": "Rival Pip", "x": 78, "y": 100, "sprite": "kid_rival", "events": {"interact": "rival_talk"}},
                ],
                "collision": [
                    {"id": "fence_top", "x": 0, "y": 0, "w": 256, "h": 16},
                    {"id": "fence_bottom", "x": 0, "y": 208, "w": 256, "h": 16},
                ],
                "triggers": [
                    {"id": "to_patch", "name": "Bug Patch", "x": 112, "y": 0, "w": 32, "h": 16, "event": "go_patch"},
                    {"id": "to_club", "name": "Bug Club", "x": 240, "y": 96, "w": 16, "h": 48, "event": "go_club"},
                ],
            },
            {
                "id": "bug_patch",
                "name": "Wild Bug Patch",
                "background": "patch_bg",
                "paint_palette": ["#14532d", "#166534", "#22c55e", "#84cc16", "#78350f", "#facc15", "#f472b6"],
                "paint": scene_patch(),
                "actors": [
                    {"id": "player_patch", "name": "You", "x": 120, "y": 196, "sprite": "kid_player", "events": {}},
                    {"id": "wild_ladybyte", "name": "Wild LadyByte", "x": 84, "y": 132, "sprite": "ladybyte", "events": {"interact": "catch_ladybyte"}},
                    {"id": "wild_beetitan", "name": "Wild Beetitan", "x": 180, "y": 140, "sprite": "beetitan", "events": {"interact": "catch_beetitan"}},
                ],
                "collision": [
                    {"id": "wall_left", "x": 0, "y": 0, "w": 16, "h": 224},
                    {"id": "wall_right", "x": 240, "y": 0, "w": 16, "h": 224},
                ],
                "triggers": [
                    {"id": "patch_to_hub", "name": "Back to Garden", "x": 112, "y": 208, "w": 32, "h": 16, "event": "return_hub"},
                ],
            },
            {
                "id": "bug_club",
                "name": "Backyard Bug Club",
                "background": "club_bg",
                "paint_palette": ["#111827", "#1f2937", "#334155", "#475569", "#94a3b8", "#fbbf24", "#fef08a"],
                "paint": scene_club(),
                "actors": [
                    {"id": "player_club", "name": "You", "x": 40, "y": 176, "sprite": "kid_player", "events": {}},
                    {"id": "judge", "name": "Judge Nia", "x": 120, "y": 78, "sprite": "kid_judge", "events": {"interact": "judge_register"}},
                    {"id": "rival_club", "name": "Rival Pip", "x": 180, "y": 104, "sprite": "kid_rival", "events": {"interact": "rival_talk"}},
                    {"id": "box_stack", "name": "Matchbox Stack", "x": 206, "y": 164, "sprite": "matchbox", "events": {"interact": "box_flavor"}},
                ],
                "collision": [
                    {"id": "club_wall_top", "x": 0, "y": 0, "w": 256, "h": 16},
                    {"id": "club_wall_left", "x": 0, "y": 0, "w": 16, "h": 224},
                    {"id": "club_wall_right", "x": 240, "y": 0, "w": 16, "h": 224},
                ],
                "triggers": [
                    {"id": "ring_gate", "name": "Battle Ring", "x": 112, "y": 112, "w": 32, "h": 24, "event": "start_round_one"},
                    {"id": "club_exit", "name": "Leave Club", "x": 16, "y": 168, "w": 16, "h": 40, "event": "club_to_hub"},
                ],
            },
            {
                "id": "battle_round_one",
                "name": "Round One Arena",
                "background": "arena1_bg",
                "paint_palette": ["#0f172a", "#1d4ed8", "#1e40af", "#60a5fa", "#f59e0b", "#fef3c7"],
                "paint": scene_battle(fill=1, ring=4, edge=5),
                "actors": [
                    {"id": "hero_round1", "name": "You", "x": 56, "y": 144, "sprite": "kid_player", "events": {}},
                    {"id": "hero_bug_round1", "name": "Your Bug", "x": 90, "y": 118, "sprite": "ladybyte", "events": {}},
                    {"id": "rival_round1", "name": "Rival Pip", "x": 180, "y": 86, "sprite": "kid_rival", "events": {}},
                    {"id": "rival_bug_round1", "name": "Pip Bug", "x": 162, "y": 110, "sprite": "mantykid", "events": {}},
                ],
                "collision": [],
                "triggers": [
                    {"id": "round1_auto", "name": "Start Round One", "x": 0, "y": 0, "w": 256, "h": 224, "event": "battle_round_one_chain"},
                ],
            },
            {
                "id": "battle_round_two",
                "name": "Final Arena",
                "background": "arena2_bg",
                "paint_palette": ["#111827", "#374151", "#6b7280", "#9ca3af", "#10b981", "#facc15"],
                "paint": scene_battle(fill=2, ring=5, edge=1),
                "actors": [
                    {"id": "hero_round2", "name": "You", "x": 56, "y": 144, "sprite": "kid_player", "events": {}},
                    {"id": "hero_bug_round2", "name": "Your Bug", "x": 92, "y": 118, "sprite": "beetitan", "events": {}},
                    {"id": "judge_round2", "name": "Judge Nia", "x": 120, "y": 64, "sprite": "kid_judge", "events": {}},
                    {"id": "champ_bug_round2", "name": "Champion Bug", "x": 162, "y": 110, "sprite": "mantykid", "events": {}},
                ],
                "collision": [],
                "triggers": [
                    {"id": "round2_auto", "name": "Start Final", "x": 0, "y": 0, "w": 256, "h": 224, "event": "battle_round_two_chain"},
                ],
            },
        ],
        "eventChains": [
            {
                "id": "title_intro",
                "name": "Title Intro",
                "trigger": {"type": "scene_start", "scene": "title"},
                "steps": [
                    {"id": "ti1", "type": "show_text", "text": "POCKET BUGS"},
                    {"id": "ti2", "type": "show_text", "text": "Catch garden bugs. Battle in matchboxes."},
                    {"id": "ti3", "type": "show_text", "text": "Step anywhere to start your bug-taming day."},
                ],
            },
            {
                "id": "start_adventure",
                "name": "Start Adventure",
                "trigger": {"type": "zone_enter", "zone": "press_start"},
                "steps": [{"id": "sa_go", "type": "change_scene", "scene": "garden_hub"}],
            },
            {
                "id": "garden_intro",
                "name": "Garden Intro",
                "trigger": {"type": "scene_start", "scene": "garden_hub"},
                "steps": [
                    {"id": "gi1", "type": "show_text", "text": "Find bugs in the patch, then join the bug club battle ring."},
                ],
            },
            {
                "id": "go_patch",
                "name": "Go Patch",
                "trigger": {"type": "zone_enter", "zone": "to_patch"},
                "steps": [{"id": "gp1", "type": "change_scene", "scene": "bug_patch"}],
            },
            {
                "id": "go_club",
                "name": "Go Club",
                "trigger": {"type": "zone_enter", "zone": "to_club"},
                "steps": [{"id": "gc1", "type": "change_scene", "scene": "bug_club"}],
            },
            {
                "id": "return_hub",
                "name": "Return Hub",
                "trigger": {"type": "zone_enter", "zone": "patch_to_hub"},
                "steps": [{"id": "rh1", "type": "change_scene", "scene": "garden_hub"}],
            },
            {
                "id": "catch_ladybyte",
                "name": "Catch LadyByte",
                "trigger": {"type": "actor_interact", "actor": "wild_ladybyte"},
                "steps": [
                    {"id": "cl1", "type": "show_text", "text": "You place LadyByte into a tiny matchbox."},
                    {"id": "cl2", "type": "set_flag", "flag": "has_bug", "value": True},
                    {"id": "cl3", "type": "set_flag", "flag": "caught_ladybyte", "value": True},
                    {"id": "cl4", "type": "set_variable", "variable": "bugs_found", "value": 1},
                    {"id": "cl5", "type": "play_sound", "sound": "buzz"},
                ],
            },
            {
                "id": "catch_beetitan",
                "name": "Catch Beetitan",
                "trigger": {"type": "actor_interact", "actor": "wild_beetitan"},
                "steps": [
                    {"id": "cb1", "type": "show_text", "text": "Beetitan settles into your matchbox with a thump."},
                    {"id": "cb2", "type": "set_flag", "flag": "has_bug", "value": True},
                    {"id": "cb3", "type": "set_flag", "flag": "caught_beetitan", "value": True},
                    {"id": "cb4", "type": "set_variable", "variable": "bugs_found", "value": 2},
                    {"id": "cb5", "type": "play_sound", "sound": "thump"},
                ],
            },
            {
                "id": "rival_talk",
                "name": "Rival Talk",
                "trigger": {"type": "actor_interact", "actor": "rival_club"},
                "steps": [{"id": "rt1", "type": "show_text", "text": "Pip: Bring your best bug to the ring."}],
            },
            {
                "id": "judge_hub_hint",
                "name": "Judge Hub Hint",
                "trigger": {"type": "actor_interact", "actor": "judge_hub"},
                "steps": [{"id": "jh1", "type": "show_text", "text": "Judge Nia: Catch a bug, then register inside the club."}],
            },
            {
                "id": "judge_register",
                "name": "Register",
                "trigger": {"type": "actor_interact", "actor": "judge"},
                "steps": [
                    {
                        "id": "jr_if",
                        "type": "if_flag",
                        "flag": "has_bug",
                        "then": [
                            {"id": "jr_t1", "type": "show_text", "text": "Judge Nia: Registered. Keep your bug boxed until battle call."},
                            {"id": "jr_t2", "type": "set_flag", "flag": "registered_for_cup", "value": True},
                        ],
                        "else": [
                            {"id": "jr_e1", "type": "show_text", "text": "Judge Nia: Catch at least one bug first."},
                        ],
                    }
                ],
            },
            {
                "id": "box_flavor",
                "name": "Matchbox Flavor",
                "trigger": {"type": "actor_interact", "actor": "box_stack"},
                "steps": [{"id": "bf1", "type": "show_text", "text": "Cardboard bug boxes stacked for kid battlers."}],
            },
            {
                "id": "club_to_hub",
                "name": "Club To Hub",
                "trigger": {"type": "zone_enter", "zone": "club_exit"},
                "steps": [{"id": "ch1", "type": "change_scene", "scene": "garden_hub"}],
            },
            {
                "id": "start_round_one",
                "name": "Start Round One",
                "trigger": {"type": "zone_enter", "zone": "ring_gate"},
                "steps": [
                    {
                        "id": "sr_if",
                        "type": "if_flag",
                        "flag": "registered_for_cup",
                        "then": [
                            {"id": "sr_t1", "type": "show_text", "text": "Round One starts. Bugs out of boxes!"},
                            {"id": "sr_t2", "type": "change_scene", "scene": "battle_round_one"},
                        ],
                        "else": [
                            {"id": "sr_e1", "type": "show_text", "text": "Register with the judge first."},
                        ],
                    }
                ],
            },
            {
                "id": "battle_round_one_chain",
                "name": "Battle Round One",
                "trigger": {"type": "zone_enter", "zone": "round1_auto"},
                "steps": [
                    {"id": "b1_1", "type": "show_text", "text": "Pip sends out Mantykid."},
                    {"id": "b1_2", "type": "show_text", "text": "You open your matchbox and send LadyByte."},
                    {"id": "b1_3", "type": "set_sprite_frame", "actor": "hero_bug_round1", "frame": "ladybyte_1"},
                    {"id": "b1_4", "type": "play_sound", "sound": "buzz"},
                    {"id": "b1_5", "type": "show_text", "text": "LadyByte uses Leaf Jab."},
                    {"id": "b1_6", "type": "wait", "frames": 20},
                    {"id": "b1_7", "type": "set_sprite_frame", "actor": "rival_bug_round1", "frame": "mantykid_1"},
                    {"id": "b1_8", "type": "show_text", "text": "Mantykid staggers. Round One win."},
                    {"id": "b1_9", "type": "set_flag", "flag": "won_round_one", "value": True},
                    {"id": "b1_10", "type": "set_variable", "variable": "wins", "value": 1},
                    {"id": "b1_11", "type": "change_scene", "scene": "battle_round_two"},
                ],
            },
            {
                "id": "battle_round_two_chain",
                "name": "Battle Final",
                "trigger": {"type": "zone_enter", "zone": "round2_auto"},
                "steps": [
                    {"id": "b2_1", "type": "show_text", "text": "Final match: champion Mantykid enters."},
                    {"id": "b2_2", "type": "set_sprite_frame", "actor": "hero_bug_round2", "frame": "beetitan_1"},
                    {"id": "b2_3", "type": "play_sound", "sound": "thump"},
                    {"id": "b2_4", "type": "show_text", "text": "Beetitan uses Shell Bash."},
                    {"id": "b2_5", "type": "set_sprite_frame", "actor": "champ_bug_round2", "frame": "mantykid_1"},
                    {"id": "b2_6", "type": "show_text", "text": "Counter hit lands, but Beetitan stands firm."},
                    {"id": "b2_7", "type": "wait", "frames": 20},
                    {"id": "b2_8", "type": "show_text", "text": "Final strike. You win the Backyard Bug Cup."},
                    {"id": "b2_9", "type": "set_flag", "flag": "won_round_two", "value": True},
                    {"id": "b2_10", "type": "set_variable", "variable": "wins", "value": 2},
                    {"id": "b2_11", "type": "show_text", "text": "Pocket Bugs demo complete."},
                ],
            },
        ],
    }


def main() -> None:
    project = build_project()
    validated = model_to_jsonable(Project.model_validate(project))

    out_main = ROOT / "examples" / "pocket-bugs" / "project.snesproj"
    out_web = ROOT / "web" / "public" / "examples" / "pocket-bugs.snesproj"
    out_main.parent.mkdir(parents=True, exist_ok=True)
    out_web.parent.mkdir(parents=True, exist_ok=True)

    text = json.dumps(validated, indent=2) + "\n"
    out_main.write_text(text, encoding="utf-8")
    out_web.write_text(text, encoding="utf-8")

    print(f"Wrote {out_main}")
    print(f"Wrote {out_web}")


if __name__ == "__main__":
    main()
