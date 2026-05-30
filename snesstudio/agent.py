from __future__ import annotations

import re
from typing import Any
from .schema import Project
from .project import load_project


def _slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return value or "helper_patch"


def propose_patch(project: Project, prompt: str) -> dict[str, Any]:
    prompt_l = prompt.lower()
    scene_id = project.scenes[0].id if project.scenes else "start"
    title = "Safe helper patch"
    changes: list[dict[str, Any]] = []

    if "robot" in prompt_l:
        title = "Add friendly robot helper"
        base_chain_id = "robot_hint_chain"
        existing_chains = {c.id for c in project.eventChains}
        chain_id = base_chain_id if base_chain_id not in existing_chains else "robot_hint_chain_2"
        base_actor_id = "friendly_robot"
        existing_actors = {a.id for scene in project.scenes for a in scene.actors}
        actor_id = base_actor_id if base_actor_id not in existing_actors else "friendly_robot_2"
        changes.extend([
            {"op": "add_actor", "scene": scene_id, "actor": {"id": actor_id, "name": "Friendly Robot", "x": 112, "y": 120, "sprite": "robot"}},
            {"op": "add_event_chain", "chain": {"id": chain_id, "name": "Robot Hint Chain", "trigger": {"type": "actor_interact", "actor": actor_id}}},
            {"op": "add_event_step", "chain": chain_id, "step": {"id": "robot_face", "type": "face_player", "actor": actor_id}},
            {"op": "add_event_step", "chain": chain_id, "step": {"id": "robot_text", "type": "show_text", "text": "Press A to talk. Press B to jump."}},
            {"op": "update_actor", "scene": scene_id, "actor_id": actor_id, "fields": {"events": {"interact": chain_id}}},
        ])
    elif "boss" in prompt_l:
        title = "Add boss scene starter"
        changes.extend([
            {"op": "add_scene", "scene": {"id": "boss_room", "name": "Boss Room"}},
            {"op": "add_event_chain", "chain": {"id": "boss_intro", "name": "Boss Intro", "trigger": {"type": "scene_start"}}},
            {"op": "add_event_step", "chain": "boss_intro", "step": {"id": "boss_text", "type": "show_text", "text": "The final challenge begins!"}},
        ])
    else:
        title = "Add learner note"
        chain_id = f"{_slug(prompt)[:24]}_chain"
        changes.extend([
            {"op": "add_event_chain", "chain": {"id": chain_id, "name": "Learner Idea", "trigger": {"type": "scene_start"}}},
            {"op": "add_event_step", "chain": chain_id, "step": {"id": "idea_text", "type": "show_text", "text": prompt[:120] or "New idea"}},
        ])

    return {
        "id": f"patch_{_slug(title)}",
        "title": title,
        "summary": "Review this patch before applying. It uses safe editor operations rather than direct code edits.",
        "risk": "low",
        "changes": changes,
    }


def propose_patch_from_file(project_path: str, prompt: str) -> dict[str, Any]:
    return propose_patch(load_project(project_path), prompt)
