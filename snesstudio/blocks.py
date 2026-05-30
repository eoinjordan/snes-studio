from __future__ import annotations

BLOCKS = [
    {"type": "show_text", "category": "Dialogue", "label": "Show text", "defaults": {"text": "Hello!"}},
    {"type": "move_actor", "category": "Actor", "label": "Move actor", "defaults": {"actor": "player", "dx": 0, "dy": 8}},
    {"type": "face_player", "category": "Actor", "label": "Face player", "defaults": {"actor": "npc"}},
    {"type": "hide_actor", "category": "Actor", "label": "Hide actor", "defaults": {"actor": "npc"}},
    {"type": "show_actor", "category": "Actor", "label": "Show actor", "defaults": {"actor": "npc"}},
    {"type": "set_sprite_frame", "category": "Actor", "label": "Set sprite frame", "defaults": {"actor": "npc", "frame": "idle_0"}},
    {"type": "change_scene", "category": "Scene", "label": "Change scene", "defaults": {"scene": "next_scene"}},
    {"type": "set_flag", "category": "Logic", "label": "Set flag", "defaults": {"flag": "met_robot", "value": True}},
    {"type": "if_flag", "category": "Logic", "label": "If flag", "defaults": {"flag": "met_robot", "then": [], "else": []}},
    {"type": "set_variable", "category": "Logic", "label": "Set variable", "defaults": {"variable": "score", "value": 1}},
    {"type": "wait", "category": "Timing", "label": "Wait", "defaults": {"frames": 30}},
    {"type": "play_sound", "category": "Sound", "label": "Play sound", "defaults": {"sound": "blip"}},
    {"type": "play_music", "category": "Sound", "label": "Play music", "defaults": {"music": "theme"}},
]


def block_palette() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for block in BLOCKS:
        out.setdefault(block["category"], []).append(block)
    return out
