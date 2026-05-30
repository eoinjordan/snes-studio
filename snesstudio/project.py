from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from .schema import Project, model_to_jsonable


def load_project(path: str | Path) -> Project:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Project.model_validate(data)


def save_project(path: str | Path, project: Project | dict[str, Any], backup: bool = False) -> Path | None:
    target = Path(path)
    backup_path: Path | None = None
    if backup and target.exists():
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_path = target.with_suffix(target.suffix + f".{stamp}.bak")
        shutil.copy2(target, backup_path)
    if isinstance(project, Project):
        data = model_to_jsonable(project)
    else:
        data = model_to_jsonable(Project.model_validate(project))
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return backup_path


def inventory(project: Project) -> dict[str, Any]:
    actor_count = sum(len(scene.actors) for scene in project.scenes)
    collision_count = sum(len(scene.collision) for scene in project.scenes)
    trigger_count = sum(len(scene.triggers) for scene in project.scenes)
    step_count = sum(len(chain.steps) for chain in project.eventChains)
    return {
        "name": project.name,
        "target": project.target,
        "scene_count": len(project.scenes),
        "actor_count": actor_count,
        "sprite_count": len(project.sprites),
        "event_chain_count": len(project.eventChains),
        "event_step_count": step_count,
        "collision_count": collision_count,
        "trigger_count": trigger_count,
        "flags": len(project.flags),
        "variables": len(project.variables),
        "scenes": [
            {
                "id": scene.id,
                "name": scene.name,
                "actors": len(scene.actors),
                "collision": len(scene.collision),
                "triggers": len(scene.triggers),
            }
            for scene in project.scenes
        ],
    }
