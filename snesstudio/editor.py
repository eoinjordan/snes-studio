from __future__ import annotations

import copy
from typing import Any
from .schema import Project, Scene, Actor, Collision, Zone, Sprite, EventChain, EventStep, Trigger, model_to_jsonable


def _clone(project: Project | dict[str, Any]) -> Project:
    if isinstance(project, Project):
        return Project.model_validate(model_to_jsonable(project))
    return Project.model_validate(copy.deepcopy(project))


def _dict(project: Project) -> dict[str, Any]:
    return model_to_jsonable(Project.model_validate(model_to_jsonable(project)))


def add_scene(project: Project | dict[str, Any], scene_id: str, name: str, background: str | None = None) -> dict[str, Any]:
    p = _clone(project)
    if any(s.id == scene_id for s in p.scenes):
        raise ValueError(f"scene already exists: {scene_id}")
    p.scenes.append(Scene(id=scene_id, name=name, background=background))
    return _dict(p)


def rename_scene(project: Project | dict[str, Any], scene_id: str, name: str) -> dict[str, Any]:
    p = _clone(project)
    for scene in p.scenes:
        if scene.id == scene_id:
            scene.name = name
            return _dict(p)
    raise KeyError(f"scene not found: {scene_id}")


def add_actor(project: Project | dict[str, Any], scene_id: str, actor_id: str, name: str, x: int = 0, y: int = 0, sprite: str | None = None) -> dict[str, Any]:
    p = _clone(project)
    scene = p.scene_by_id(scene_id)
    if any(a.id == actor_id for a in scene.actors):
        raise ValueError(f"actor already exists in {scene_id}: {actor_id}")
    scene.actors.append(Actor(id=actor_id, name=name, x=x, y=y, sprite=sprite))
    return _dict(p)


def update_actor(project: Project | dict[str, Any], scene_id: str, actor_id: str, **fields: Any) -> dict[str, Any]:
    p = _clone(project)
    scene = p.scene_by_id(scene_id)
    for actor in scene.actors:
        if actor.id == actor_id:
            data = actor.model_dump()
            data.update({k: v for k, v in fields.items() if v is not None})
            updated = Actor.model_validate(data)
            actor.name = updated.name
            actor.x = updated.x
            actor.y = updated.y
            actor.sprite = updated.sprite
            actor.direction = updated.direction
            actor.events = updated.events
            return _dict(p)
    raise KeyError(f"actor not found: {actor_id}")


def delete_actor(project: Project | dict[str, Any], scene_id: str, actor_id: str) -> dict[str, Any]:
    p = _clone(project)
    scene = p.scene_by_id(scene_id)
    before = len(scene.actors)
    scene.actors = [a for a in scene.actors if a.id != actor_id]
    if len(scene.actors) == before:
        raise KeyError(f"actor not found: {actor_id}")
    return _dict(p)


def add_collision(project: Project | dict[str, Any], scene_id: str, collision_id: str, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    p = _clone(project)
    scene = p.scene_by_id(scene_id)
    scene.collision.append(Collision(id=collision_id, x=x, y=y, w=w, h=h))
    return _dict(p)


def add_trigger(project: Project | dict[str, Any], scene_id: str, trigger_id: str, name: str, x: int, y: int, w: int, h: int, event: str | None = None) -> dict[str, Any]:
    p = _clone(project)
    scene = p.scene_by_id(scene_id)
    scene.triggers.append(Zone(id=trigger_id, name=name, x=x, y=y, w=w, h=h, event=event))
    return _dict(p)


def add_sprite(project: Project | dict[str, Any], sprite: dict[str, Any]) -> dict[str, Any]:
    p = _clone(project)
    s = Sprite.model_validate(sprite)
    if any(existing.id == s.id for existing in p.sprites):
        raise ValueError(f"sprite already exists: {s.id}")
    p.sprites.append(s)
    return _dict(p)


def update_sprite(project: Project | dict[str, Any], sprite_id: str, sprite: dict[str, Any]) -> dict[str, Any]:
    p = _clone(project)
    updated = Sprite.model_validate({"id": sprite_id, **sprite})
    for idx, existing in enumerate(p.sprites):
        if existing.id == sprite_id:
            p.sprites[idx] = updated
            return _dict(p)
    raise KeyError(f"sprite not found: {sprite_id}")


def add_event_chain(project: Project | dict[str, Any], chain_id: str, name: str, trigger: dict[str, Any] | None = None) -> dict[str, Any]:
    p = _clone(project)
    if any(c.id == chain_id for c in p.eventChains):
        raise ValueError(f"event chain already exists: {chain_id}")
    p.eventChains.append(EventChain(id=chain_id, name=name, trigger=Trigger.model_validate(trigger) if trigger else None))
    return _dict(p)


def add_event_step(project: Project | dict[str, Any], chain_id: str, step: dict[str, Any]) -> dict[str, Any]:
    p = _clone(project)
    chain = p.chain_by_id(chain_id)
    chain.steps.append(EventStep.model_validate(step))
    return _dict(p)


def update_event_step(project: Project | dict[str, Any], chain_id: str, step_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    p = _clone(project)
    chain = p.chain_by_id(chain_id)
    for i, step in enumerate(chain.steps):
        if step.id == step_id:
            data = step.model_dump(by_alias=True)
            data.update(fields)
            chain.steps[i] = EventStep.model_validate(data)
            return _dict(p)
    raise KeyError(f"step not found: {step_id}")


def delete_event_step(project: Project | dict[str, Any], chain_id: str, step_id: str) -> dict[str, Any]:
    p = _clone(project)
    chain = p.chain_by_id(chain_id)
    before = len(chain.steps)
    chain.steps = [s for s in chain.steps if s.id != step_id]
    if len(chain.steps) == before:
        raise KeyError(f"step not found: {step_id}")
    return _dict(p)


def reorder_event_step(project: Project | dict[str, Any], chain_id: str, step_id: str, new_index: int) -> dict[str, Any]:
    p = _clone(project)
    chain = p.chain_by_id(chain_id)
    steps = chain.steps
    for i, step in enumerate(steps):
        if step.id == step_id:
            item = steps.pop(i)
            steps.insert(max(0, min(new_index, len(steps))), item)
            return _dict(p)
    raise KeyError(f"step not found: {step_id}")
