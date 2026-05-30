"""Desktop playthrough simulator.

Runs a SNES Studio project's scene/event-chain model end to end in plain Python
— no SNES toolchain required. It interprets exactly the same data the C exporter
turns into a ROM (scenes, actors, triggers, event chains, flags, variables), so a
playthrough here mirrors what the generated game does.

Two modes:
* auto   — walks the whole story deterministically (enter scenes, talk to every
           actor, follow change_scene / zone transitions) and prints the script.
* interactive — you pick which actor to talk to / zone to enter at each scene.

Used by the CLI ``snes-studio play`` command and by the tests.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .schema import Project, EventChain, EventStep, Scene, Actor, Zone
from .project import load_project


@dataclass
class Playthrough:
    """Captured result of a run: every emitted line plus final game state."""
    lines: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    scenes_visited: list[str] = field(default_factory=list)

    def text(self) -> str:
        return "\n".join(self.lines)


def _truthy(value: Any) -> bool:
    return bool(value) and value not in (0, "0", "false", "False")


class _Engine:
    def __init__(self, project: Project, emit: Callable[[str], None]):
        self.project = project
        self.emit = emit
        self.flags: dict[str, bool] = {k: _truthy(v) for k, v in project.flags.items()}
        self.variables: dict[str, Any] = dict(project.variables)
        self.scenes: dict[str, Scene] = {s.id: s for s in project.scenes}
        self.chains: list[EventChain] = list(project.eventChains)
        self.fired: set[str] = set()

    def chain_by_id(self, cid: str | None) -> EventChain | None:
        return next((c for c in self.chains if c.id == cid), None) if cid else None

    def actor_chain(self, actor: Actor) -> EventChain | None:
        cid = (actor.events or {}).get("interact")
        chain = self.chain_by_id(cid)
        if chain:
            return chain
        return next((c for c in self.chains
                     if c.trigger and c.trigger.type == "actor_interact" and c.trigger.actor == actor.id), None)

    def zone_chain(self, zone: Zone) -> EventChain | None:
        chain = self.chain_by_id(zone.event)
        if chain:
            return chain
        return next((c for c in self.chains
                     if c.trigger and c.trigger.type == "zone_enter" and c.trigger.zone == zone.id), None)

    def scene_start_chains(self, scene: Scene, first: bool) -> list[EventChain]:
        out = []
        for c in self.chains:
            t = c.trigger
            if not t or t.type != "scene_start":
                continue
            if t.scene == scene.id or (t.scene is None and first):
                out.append(c)
        return out

    def run_steps(self, steps: list[EventStep], depth: int = 1) -> str | None:
        """Execute steps; return a scene id if a change_scene fires, else None."""
        pad = "    " * depth
        for st in steps:
            t = st.type
            if t == "show_text":
                self.emit(f'{pad}{st.text}')
            elif t == "set_flag":
                self.flags[st.flag] = _truthy(st.value)
            elif t == "set_variable":
                self.variables[st.variable] = st.value
            elif t == "if_flag":
                branch = st.then if self.flags.get(st.flag) else st.else_
                got = self.run_steps(branch, depth + 1)
                if got:
                    return got
            elif t == "change_scene":
                return st.scene
            elif t == "wait":
                pass
            elif t == "play_sound":
                self.emit(f'{pad}♪ ({st.sound})')
            elif t == "play_music":
                self.emit(f'{pad}♪ ~{st.music}~')
            # face_player / move_actor / hide / show / set_sprite_frame: silent stage directions
        return None


def play_auto(project: Project, emit: Callable[[str], None] | None = None, max_hops: int = 40) -> Playthrough:
    result = Playthrough()

    def out(s: str) -> None:
        result.lines.append(s)
        if emit:
            emit(s)

    eng = _Engine(project, out)
    if not project.scenes:
        return result

    current: str | None = project.scenes[0].id
    hops = 0
    while current and hops < max_hops:
        hops += 1
        scene = eng.scenes.get(current)
        if not scene:
            break
        result.scenes_visited.append(scene.id)
        out(f"\n=== {scene.name} ===")
        nxt: str | None = None

        # 1) scene-start chains for this scene
        for c in eng.scene_start_chains(scene, first=(hops == 1)):
            if c.id in eng.fired:
                continue
            eng.fired.add(c.id)
            nxt = eng.run_steps(c.steps)
            if nxt:
                break
        if nxt:
            current = nxt
            continue

        # 2) talk to each actor that has dialogue (in placement order)
        for actor in scene.actors:
            chain = eng.actor_chain(actor)
            if not chain or chain.id in eng.fired:
                continue
            eng.fired.add(chain.id)
            out(f"-- Talk to {actor.name} --")
            nxt = eng.run_steps(chain.steps)
            if nxt:
                break
        if nxt:
            current = nxt
            continue

        # 3) step into a trigger zone to advance the story
        for zone in scene.triggers:
            chain = eng.zone_chain(zone)
            if not chain or chain.id in eng.fired:
                continue
            eng.fired.add(chain.id)
            out(f"-- Enter: {zone.name} --")
            nxt = eng.run_steps(chain.steps)
            if nxt:
                break
        current = nxt

    result.flags = eng.flags
    result.variables = eng.variables
    out(f"\n=== THE END ===")
    if "rescued" in eng.variables:
        out(f"Poachermon rescued: {eng.variables['rescued']}")
    won = [k for k, v in eng.flags.items() if v]
    if won:
        out(f"Story flags set: {', '.join(won)}")
    return result


def play_from_file(project_path: str | Path, emit: Callable[[str], None] | None = None) -> Playthrough:
    return play_auto(load_project(project_path), emit)
