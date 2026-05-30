from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from . import __version__
from .schema import Project, model_to_jsonable
from .project import load_project, save_project, inventory
from .compiler import export_c, make_rom
from .assets import export_assets
from .tilemap import export_tilemaps
from .agent import propose_patch
from .patches import apply_patch as apply_patch_data
from . import editor


def print_result(data: Any, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(data, indent=2))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {v}")
        else:
            print(data)


def load_data(path: str) -> dict[str, Any]:
    return model_to_jsonable(load_project(path))


def write_data(path: str, data: dict[str, Any]) -> None:
    save_project(path, Project.model_validate(data), backup=True)


def cmd_validate(args):
    project = load_project(args.project)
    print_result({"valid": True, "name": project.name, "version": project.schema_version}, args.json)


def cmd_inventory(args):
    print_result(inventory(load_project(args.project)), args.json)


def cmd_export_c(args):
    print_result(export_c(args.project, args.out_dir), args.json)


def cmd_make_rom(args):
    print_result(make_rom(args.project, args.out_file, args.skip_build), args.json)


def cmd_export_assets(args):
    print_result(export_assets(args.project, args.out_dir), args.json)


def cmd_export_tilemaps(args):
    print_result(export_tilemaps(args.project, args.out_dir), args.json)


def cmd_propose(args):
    patch = propose_patch(load_project(args.project), args.prompt)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
    print_result(patch, args.json)


def cmd_review_patch(args):
    patch = json.loads(Path(args.patch).read_text(encoding="utf-8"))
    print_result({"title": patch.get("title"), "summary": patch.get("summary"), "changes": patch.get("changes", [])}, args.json)


def cmd_apply_patch(args):
    data = load_data(args.project)
    patch = json.loads(Path(args.patch).read_text(encoding="utf-8"))
    next_data = apply_patch_data(data, patch)
    write_data(args.project, next_data)
    print_result({"applied": True, "changes": len(patch.get("changes", []))}, args.json)


def cmd_add_scene(args):
    data = editor.add_scene(load_data(args.project), args.id, args.name, args.background)
    write_data(args.project, data)
    print_result({"added_scene": args.id}, args.json)


def cmd_add_actor(args):
    data = editor.add_actor(load_data(args.project), args.scene, args.id, args.name, args.x, args.y, args.sprite)
    write_data(args.project, data)
    print_result({"added_actor": args.id, "scene": args.scene}, args.json)


def cmd_add_collision(args):
    data = editor.add_collision(load_data(args.project), args.scene, args.id, args.x, args.y, args.w, args.h)
    write_data(args.project, data)
    print_result({"added_collision": args.id}, args.json)


def cmd_add_trigger(args):
    data = editor.add_trigger(load_data(args.project), args.scene, args.id, args.name, args.x, args.y, args.w, args.h, args.event)
    write_data(args.project, data)
    print_result({"added_trigger": args.id}, args.json)


def cmd_add_event_chain(args):
    trigger = {"type": args.trigger_type} if args.trigger_type else None
    data = editor.add_event_chain(load_data(args.project), args.id, args.name, trigger)
    write_data(args.project, data)
    print_result({"added_event_chain": args.id}, args.json)


def cmd_add_step(args):
    step = {"id": args.id, "type": args.type}
    for key in ["text", "scene", "actor", "flag", "sound", "music", "frame"]:
        value = getattr(args, key, None)
        if value is not None:
            step[key] = value
    if args.dx is not None: step["dx"] = args.dx
    if args.dy is not None: step["dy"] = args.dy
    if args.value is not None:
        if args.value.lower() in ("true", "false"):
            step["value"] = args.value.lower() == "true"
        else:
            step["value"] = args.value
    if args.frames is not None: step["frames"] = args.frames
    data = editor.add_event_step(load_data(args.project), args.chain, step)
    write_data(args.project, data)
    print_result({"added_step": args.id, "chain": args.chain}, args.json)


def cmd_blocks(args):
    from .blocks import block_palette
    print_result(block_palette(), args.json)


def cmd_play(args):
    from .sim import play_auto
    project = load_project(args.project)
    run = play_auto(project, emit=None if args.json else print)
    if args.json:
        print(json.dumps({
            "scenes_visited": run.scenes_visited,
            "flags": run.flags,
            "variables": run.variables,
            "lines": run.lines,
        }, indent=2))


def cmd_serve(args):
    try:
        from .server import run_server
    except Exception as exc:
        raise SystemExit("Install server extras first: pip install -e '.[server]'") from exc
    run_server(args.project, args.host, args.port)


def build_parser():
    p = argparse.ArgumentParser(prog="snes-studio", description="SNES Studio CLI")
    p.add_argument("--version", action="version", version=f"SNES Studio {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp):
        sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("validate"); sp.add_argument("project"); common(sp); sp.set_defaults(func=cmd_validate)
    sp = sub.add_parser("inventory"); sp.add_argument("project"); common(sp); sp.set_defaults(func=cmd_inventory)
    sp = sub.add_parser("export-c"); sp.add_argument("project"); sp.add_argument("out_dir"); common(sp); sp.set_defaults(func=cmd_export_c)
    sp = sub.add_parser("export-assets"); sp.add_argument("project"); sp.add_argument("out_dir"); common(sp); sp.set_defaults(func=cmd_export_assets)
    sp = sub.add_parser("export-tilemaps"); sp.add_argument("project"); sp.add_argument("out_dir"); common(sp); sp.set_defaults(func=cmd_export_tilemaps)
    sp = sub.add_parser("make:rom"); sp.add_argument("project"); sp.add_argument("out_file"); sp.add_argument("--skip-build", action="store_true"); common(sp); sp.set_defaults(func=cmd_make_rom)
    sp = sub.add_parser("propose"); sp.add_argument("project"); sp.add_argument("prompt"); sp.add_argument("--out"); common(sp); sp.set_defaults(func=cmd_propose)
    sp = sub.add_parser("review-patch"); sp.add_argument("patch"); common(sp); sp.set_defaults(func=cmd_review_patch)
    sp = sub.add_parser("apply-patch"); sp.add_argument("project"); sp.add_argument("patch"); common(sp); sp.set_defaults(func=cmd_apply_patch)
    sp = sub.add_parser("blocks"); common(sp); sp.set_defaults(func=cmd_blocks)
    sp = sub.add_parser("play", help="Play the project end to end in the terminal (desktop simulator)"); sp.add_argument("project"); common(sp); sp.set_defaults(func=cmd_play)

    sp = sub.add_parser("add-scene"); sp.add_argument("project"); sp.add_argument("--id", required=True); sp.add_argument("--name", required=True); sp.add_argument("--background"); common(sp); sp.set_defaults(func=cmd_add_scene)
    sp = sub.add_parser("add-actor"); sp.add_argument("project"); sp.add_argument("--scene", required=True); sp.add_argument("--id", required=True); sp.add_argument("--name", required=True); sp.add_argument("--x", type=int, default=0); sp.add_argument("--y", type=int, default=0); sp.add_argument("--sprite"); common(sp); sp.set_defaults(func=cmd_add_actor)
    sp = sub.add_parser("add-collision"); sp.add_argument("project"); sp.add_argument("--scene", required=True); sp.add_argument("--id", required=True); sp.add_argument("--x", type=int, default=0); sp.add_argument("--y", type=int, default=0); sp.add_argument("--w", type=int, default=16); sp.add_argument("--h", type=int, default=16); common(sp); sp.set_defaults(func=cmd_add_collision)
    sp = sub.add_parser("add-trigger"); sp.add_argument("project"); sp.add_argument("--scene", required=True); sp.add_argument("--id", required=True); sp.add_argument("--name", default="Trigger Zone"); sp.add_argument("--x", type=int, default=0); sp.add_argument("--y", type=int, default=0); sp.add_argument("--w", type=int, default=16); sp.add_argument("--h", type=int, default=16); sp.add_argument("--event"); common(sp); sp.set_defaults(func=cmd_add_trigger)
    sp = sub.add_parser("add-event-chain"); sp.add_argument("project"); sp.add_argument("--id", required=True); sp.add_argument("--name", required=True); sp.add_argument("--trigger-type"); common(sp); sp.set_defaults(func=cmd_add_event_chain)
    sp = sub.add_parser("add-step"); sp.add_argument("project"); sp.add_argument("--chain", required=True); sp.add_argument("--id", required=True); sp.add_argument("--type", required=True); sp.add_argument("--text"); sp.add_argument("--scene"); sp.add_argument("--actor"); sp.add_argument("--flag"); sp.add_argument("--value"); sp.add_argument("--dx", type=int); sp.add_argument("--dy", type=int); sp.add_argument("--frames", type=int); sp.add_argument("--sound"); sp.add_argument("--music"); sp.add_argument("--frame"); common(sp); sp.set_defaults(func=cmd_add_step)
    sp = sub.add_parser("serve"); sp.add_argument("project"); sp.add_argument("--host", default="127.0.0.1"); sp.add_argument("--port", type=int, default=8765); sp.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except Exception as exc:
        if getattr(args, "json", False):
            print(json.dumps({"error": str(exc)}), file=sys.stderr)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
