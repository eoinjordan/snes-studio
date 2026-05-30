from __future__ import annotations

from typing import Any
from . import editor


def apply_patch(project: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    current: dict[str, Any] = project
    for change in patch.get("changes", []):
        op = change.get("op")
        if op == "add_scene":
            scene = change["scene"]
            current = editor.add_scene(current, scene["id"], scene.get("name", scene["id"]), scene.get("background"))
        elif op == "add_actor":
            actor = change["actor"]
            current = editor.add_actor(current, change["scene"], actor["id"], actor.get("name", actor["id"]), actor.get("x", 0), actor.get("y", 0), actor.get("sprite"))
        elif op == "update_actor":
            current = editor.update_actor(current, change["scene"], change["actor_id"], **change.get("fields", {}))
        elif op == "add_collision":
            c = change["collision"]
            current = editor.add_collision(current, change["scene"], c["id"], c.get("x", 0), c.get("y", 0), c.get("w", 16), c.get("h", 16))
        elif op == "add_trigger":
            t = change["trigger"]
            current = editor.add_trigger(current, change["scene"], t["id"], t.get("name", t["id"]), t.get("x", 0), t.get("y", 0), t.get("w", 16), t.get("h", 16), t.get("event"))
        elif op == "add_sprite":
            current = editor.add_sprite(current, change["sprite"])
        elif op == "update_sprite":
            current = editor.update_sprite(current, change["sprite_id"], change["sprite"])
        elif op == "add_event_chain":
            chain = change["chain"]
            current = editor.add_event_chain(current, chain["id"], chain.get("name", chain["id"]), chain.get("trigger"))
        elif op == "add_event_step":
            current = editor.add_event_step(current, change["chain"], change["step"])
        elif op == "update_event_step":
            current = editor.update_event_step(current, change["chain"], change["step_id"], change.get("fields", {}))
        elif op == "delete_event_step":
            current = editor.delete_event_step(current, change["chain"], change["step_id"])
        else:
            raise ValueError(f"unsupported patch op: {op}")
    return current
