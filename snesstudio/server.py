from __future__ import annotations

from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from .project import load_project, save_project, inventory
from .schema import Project, model_to_jsonable
from .blocks import block_palette
from .agent import propose_patch
from .patches import apply_patch
from .compiler import export_c, make_rom
from . import editor

class PromptRequest(BaseModel):
    prompt: str

class PatchRequest(BaseModel):
    patch: dict[str, Any]

class ProjectRequest(BaseModel):
    project: dict[str, Any]

class SceneRequest(BaseModel):
    id: str
    name: str
    background: str | None = None

class SceneUpdateRequest(BaseModel):
    name: str | None = None
    background: str | None = None
    paint: list[int] | None = None
    notes: str | None = None

class ActorRequest(BaseModel):
    id: str
    name: str
    x: int = 0
    y: int = 0
    sprite: str | None = None
    events: dict[str, str] | None = None

class RectRequest(BaseModel):
    id: str
    x: int = 0
    y: int = 0
    w: int = 16
    h: int = 16

class TriggerRequest(RectRequest):
    name: str = "Trigger Zone"
    event: str | None = None

class ChainRequest(BaseModel):
    id: str
    name: str
    trigger: dict[str, Any] | None = None

class StepRequest(BaseModel):
    step: dict[str, Any]

class SpriteRequest(BaseModel):
    sprite: dict[str, Any]

class BuildRequest(BaseModel):
    skip_build: bool = True
    out_file: str = "build/web-preview.sfc"


def create_app(project_path: str) -> FastAPI:
    path = Path(project_path)
    app = FastAPI(title="SNES Studio API", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    def read() -> Project:
        return load_project(path)

    def write(data: dict[str, Any]) -> str | None:
        backup = save_project(path, Project.model_validate(data), backup=True)
        return str(backup) if backup else None

    @app.get("/api/health")
    def health(): return {"ok": True, "project": str(path)}

    @app.get("/api/project")
    def get_project(): return model_to_jsonable(read())

    @app.post("/api/project")
    def replace_project(req: ProjectRequest):
        project = Project.model_validate(req.project)
        backup = save_project(path, project, backup=True)
        return {
            "backup": str(backup) if backup else None,
            "project": model_to_jsonable(project),
            "inventory": inventory(project),
        }

    @app.get("/api/inventory")
    def get_inventory(): return inventory(read())

    @app.get("/api/blocks")
    def get_blocks(): return block_palette()

    @app.post("/api/propose")
    def api_propose(req: PromptRequest): return propose_patch(read(), req.prompt)

    @app.post("/api/apply-patch")
    def api_apply(req: PatchRequest):
        try:
            next_data = apply_patch(model_to_jsonable(read()), req.patch)
            backup = write(next_data)
            return {"applied": True, "backup": backup, "project": next_data}
        except Exception as exc: raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/export-c")
    def api_export_c(): return export_c(path, "build/generated/web")

    @app.post("/api/make-rom")
    def api_make_rom(req: BuildRequest): return make_rom(path, req.out_file, req.skip_build)

    @app.post("/api/scenes")
    def api_add_scene(req: SceneRequest):
        data = editor.add_scene(model_to_jsonable(read()), req.id, req.name, req.background); backup = write(data); return {"backup": backup, "project": data}

    @app.patch("/api/scenes/{scene_id}")
    def api_update_scene(scene_id: str, req: SceneUpdateRequest):
        try:
            data = editor.update_scene(model_to_jsonable(read()), scene_id, name=req.name, background=req.background, paint=req.paint, notes=req.notes); backup = write(data); return {"backup": backup, "project": data}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/scenes/{scene_id}/actors")
    def api_add_actor(scene_id: str, req: ActorRequest):
        data = editor.add_actor(model_to_jsonable(read()), scene_id, req.id, req.name, req.x, req.y, req.sprite); backup = write(data); return {"backup": backup, "project": data}

    @app.patch("/api/scenes/{scene_id}/actors/{actor_id}")
    def api_update_actor(scene_id: str, actor_id: str, req: ActorRequest):
        data = editor.update_actor(model_to_jsonable(read()), scene_id, actor_id, name=req.name, x=req.x, y=req.y, sprite=req.sprite, events=req.events); backup = write(data); return {"backup": backup, "project": data}

    @app.delete("/api/scenes/{scene_id}/actors/{actor_id}")
    def api_delete_actor(scene_id: str, actor_id: str):
        data = editor.delete_actor(model_to_jsonable(read()), scene_id, actor_id); backup = write(data); return {"backup": backup, "project": data}

    @app.post("/api/scenes/{scene_id}/collision")
    def api_collision(scene_id: str, req: RectRequest):
        data = editor.add_collision(model_to_jsonable(read()), scene_id, req.id, req.x, req.y, req.w, req.h); backup = write(data); return {"backup": backup, "project": data}

    @app.patch("/api/scenes/{scene_id}/collision/{collision_id}")
    def api_update_collision(scene_id: str, collision_id: str, req: RectRequest):
        try:
            data = editor.update_collision(model_to_jsonable(read()), scene_id, collision_id, x=req.x, y=req.y, w=req.w, h=req.h); backup = write(data); return {"backup": backup, "project": data}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

    @app.delete("/api/scenes/{scene_id}/collision/{collision_id}")
    def api_delete_collision(scene_id: str, collision_id: str):
        try:
            data = editor.delete_collision(model_to_jsonable(read()), scene_id, collision_id); backup = write(data); return {"backup": backup, "project": data}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/scenes/{scene_id}/triggers")
    def api_trigger(scene_id: str, req: TriggerRequest):
        data = editor.add_trigger(model_to_jsonable(read()), scene_id, req.id, req.name, req.x, req.y, req.w, req.h, req.event); backup = write(data); return {"backup": backup, "project": data}

    @app.patch("/api/scenes/{scene_id}/triggers/{trigger_id}")
    def api_update_trigger(scene_id: str, trigger_id: str, req: TriggerRequest):
        try:
            data = editor.update_trigger(model_to_jsonable(read()), scene_id, trigger_id, name=req.name, x=req.x, y=req.y, w=req.w, h=req.h, event=req.event); backup = write(data); return {"backup": backup, "project": data}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

    @app.delete("/api/scenes/{scene_id}/triggers/{trigger_id}")
    def api_delete_trigger(scene_id: str, trigger_id: str):
        try:
            data = editor.delete_trigger(model_to_jsonable(read()), scene_id, trigger_id); backup = write(data); return {"backup": backup, "project": data}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/event-chains")
    def api_chain(req: ChainRequest):
        data = editor.add_event_chain(model_to_jsonable(read()), req.id, req.name, req.trigger); backup = write(data); return {"backup": backup, "project": data}

    @app.post("/api/event-chains/{chain_id}/steps")
    def api_step(chain_id: str, req: StepRequest):
        data = editor.add_event_step(model_to_jsonable(read()), chain_id, req.step); backup = write(data); return {"backup": backup, "project": data}

    @app.delete("/api/event-chains/{chain_id}/steps/{step_id}")
    def api_delete_step(chain_id: str, step_id: str):
        try:
            data = editor.delete_event_step(model_to_jsonable(read()), chain_id, step_id); backup = write(data); return {"backup": backup, "project": data}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/sprites")
    def api_add_sprite(req: SpriteRequest):
        try:
            data = editor.add_sprite(model_to_jsonable(read()), req.sprite); backup = write(data); return {"backup": backup, "project": data}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))

    @app.put("/api/sprites/{sprite_id}")
    def api_update_sprite(sprite_id: str, req: SpriteRequest):
        try:
            data = editor.update_sprite(model_to_jsonable(read()), sprite_id, req.sprite); backup = write(data); return {"backup": backup, "project": data}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

    return app


def run_server(project_path: str, host: str = "127.0.0.1", port: int = 8765) -> None:
    uvicorn.run(create_app(project_path), host=host, port=port)
