from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

Button = Literal["A", "B", "X", "Y", "L", "R", "START", "SELECT"]
ActionType = Literal[
    "show_text", "change_scene", "move_actor", "face_player", "set_flag", "if_flag",
    "set_variable", "wait", "play_sound", "play_music", "hide_actor", "show_actor",
    "set_sprite_frame", "comment"
]
TriggerType = Literal["scene_start", "actor_interact", "zone_enter", "button_press", "update"]

class Rect(BaseModel):
    x: int = 0
    y: int = 0
    w: int = 16
    h: int = 16

class RomSettings(BaseModel):
    title: str = "SNESSTUDIO"
    region: Literal["NTSC", "PAL"] = "NTSC"

class LearnerSettings(BaseModel):
    age_band: str = "kids"
    require_human_review: bool = True
    mentor_notes: list[str] = Field(default_factory=lambda: ["Review helper patches before applying."])

class PixelFrame(BaseModel):
    id: str
    name: str = "Frame"
    pixels: list[int] = Field(default_factory=list)

class Sprite(BaseModel):
    id: str
    name: str
    width: int = 16
    height: int = 16
    palette: list[str] = Field(default_factory=lambda: ["#000000", "#64748b", "#67e8f9", "#ffffff"])
    frames: list[PixelFrame] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_frames(self) -> "Sprite":
        area = self.width * self.height
        if not self.frames:
            self.frames = [PixelFrame(id="idle_0", name="Idle 0", pixels=[0] * area)]
        for frame in self.frames:
            if not frame.pixels:
                frame.pixels = [0] * area
            if len(frame.pixels) != area:
                raise ValueError(f"sprite frame {frame.id} must have {area} pixels")
        return self

class Trigger(BaseModel):
    type: TriggerType
    actor: str | None = None
    zone: str | None = None
    button: Button | None = None
    scene: str | None = None

class EventStep(BaseModel):
    id: str
    type: ActionType
    text: str | None = None
    scene: str | None = None
    actor: str | None = None
    dx: int | None = None
    dy: int | None = None
    direction: str | None = None
    flag: str | None = None
    variable: str | None = None
    value: bool | int | str | None = None
    frames: int | None = None
    sound: str | None = None
    music: str | None = None
    frame: str | None = None
    then: list["EventStep"] = Field(default_factory=list)
    else_: list["EventStep"] = Field(default_factory=list, alias="else")

class EventChain(BaseModel):
    id: str
    name: str
    trigger: Trigger | None = None
    steps: list[EventStep] = Field(default_factory=list)
    notes: str | None = None

class Actor(BaseModel):
    id: str
    name: str
    x: int = 0
    y: int = 0
    sprite: str | None = None
    direction: str = "down"
    events: dict[str, str] = Field(default_factory=dict)

class Collision(Rect):
    id: str

class Zone(Rect):
    id: str
    name: str = "Trigger Zone"
    event: str | None = None

class Scene(BaseModel):
    id: str
    name: str
    background: str | None = None
    actors: list[Actor] = Field(default_factory=list)
    collision: list[Collision] = Field(default_factory=list)
    triggers: list[Zone] = Field(default_factory=list)
    paint: list[int] = Field(default_factory=lambda: [0] * (32 * 28))
    paint_palette: list[str] | None = None  # per-scene tile colors (index 0..n); None = editor default
    # Tile-based background (Zelda/Pokemon style): 16x14 grid of metatile indices
    # into a bundled tileset. Empty = fall back to the flat-colour `paint` grid.
    tilemap: list[int] = Field(default_factory=list)
    tileset: str | None = None  # bundled tileset id (e.g. "overworld"); None = default
    notes: str | None = None

    @field_validator("actors")
    @classmethod
    def unique_actor_ids(cls, value: list[Actor]) -> list[Actor]:
        ids = [actor.id for actor in value]
        if len(ids) != len(set(ids)):
            raise ValueError("actor ids must be unique within a scene")
        return value

    @field_validator("paint")
    @classmethod
    def valid_paint_size(cls, value: list[int]) -> list[int]:
        expected = 32 * 28
        if len(value) != expected:
            raise ValueError(f"scene paint must have {expected} cells")
        return value

    @field_validator("tilemap")
    @classmethod
    def valid_tilemap_size(cls, value: list[int]) -> list[int]:
        expected = 16 * 14
        if value and len(value) != expected:
            raise ValueError(f"scene tilemap must be empty or have {expected} cells")
        return value

class Asset(BaseModel):
    id: str
    name: str
    type: Literal["background", "sprite", "sound", "music", "font", "other"]
    path: str | None = None
    notes: str | None = None

class Project(BaseModel):
    schema_version: str = "1.0"
    name: str
    target: Literal["snes"] = "snes"
    rom: RomSettings = Field(default_factory=RomSettings)
    learner: LearnerSettings = Field(default_factory=LearnerSettings)
    scenes: list[Scene] = Field(default_factory=list)
    sprites: list[Sprite] = Field(default_factory=list)
    eventChains: list[EventChain] = Field(default_factory=list)
    assets: list[Asset] = Field(default_factory=list)
    flags: dict[str, bool] = Field(default_factory=dict)
    variables: dict[str, int | str | bool] = Field(default_factory=dict)

    @field_validator("scenes")
    @classmethod
    def unique_scene_ids(cls, value: list[Scene]) -> list[Scene]:
        ids = [scene.id for scene in value]
        if len(ids) != len(set(ids)):
            raise ValueError("scene ids must be unique")
        return value

    @field_validator("eventChains")
    @classmethod
    def unique_chain_ids(cls, value: list[EventChain]) -> list[EventChain]:
        ids = [chain.id for chain in value]
        if len(ids) != len(set(ids)):
            raise ValueError("event chain ids must be unique")
        return value

    def scene_by_id(self, scene_id: str) -> Scene:
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        raise KeyError(f"Scene not found: {scene_id}")

    def chain_by_id(self, chain_id: str) -> EventChain:
        for chain in self.eventChains:
            if chain.id == chain_id:
                return chain
        raise KeyError(f"Event chain not found: {chain_id}")


def model_to_jsonable(project: Project) -> dict[str, Any]:
    return project.model_dump(mode="json", by_alias=True, exclude_none=True)
