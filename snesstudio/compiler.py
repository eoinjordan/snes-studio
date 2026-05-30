from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .schema import Project, EventStep
from .project import load_project

TEMPLATE_DIR = Path(__file__).parent / "templates"


def c_ident(value: str) -> str:
    out = []
    for ch in value:
        if ch.isalnum() or ch == "_":
            out.append(ch.lower())
        else:
            out.append("_")
    s = "".join(out).strip("_") or "item"
    if s[0].isdigit():
        s = "_" + s
    return s


def quote(value: Any) -> str:
    return str(value or "").replace('\\', '\\\\').replace('"', '\\"')


def emit_step(step: EventStep, indent: int = 4) -> list[str]:
    pad = " " * indent
    lines: list[str] = []
    if step.type == "show_text":
        lines.append(f'{pad}snesstudio_show_text("{quote(step.text)}");')
    elif step.type == "change_scene":
        lines.append(f'{pad}snesstudio_change_scene("{quote(step.scene)}");')
    elif step.type == "move_actor":
        lines.append(f'{pad}snesstudio_move_actor("{quote(step.actor)}", {step.dx or 0}, {step.dy or 0});')
    elif step.type == "face_player":
        lines.append(f'{pad}snesstudio_face_player("{quote(step.actor)}");')
    elif step.type == "set_flag":
        value = 1 if bool(step.value) else 0
        lines.append(f'{pad}snesstudio_set_flag("{quote(step.flag)}", {value});')
    elif step.type == "if_flag":
        lines.append(f'{pad}if (snesstudio_get_flag("{quote(step.flag)}")) {{')
        for child in step.then:
            lines.extend(emit_step(child, indent + 4))
        lines.append(f'{pad}}} else {{')
        for child in step.else_:
            lines.extend(emit_step(child, indent + 4))
        lines.append(f'{pad}}}')
    elif step.type == "wait":
        lines.append(f'{pad}snesstudio_wait({step.frames or 30});')
    elif step.type == "play_sound":
        lines.append(f'{pad}snesstudio_play_sound("{quote(step.sound)}");')
    elif step.type == "play_music":
        lines.append(f'{pad}snesstudio_play_music("{quote(step.music)}");')
    elif step.type == "hide_actor":
        lines.append(f'{pad}snesstudio_hide_actor("{quote(step.actor)}");')
    elif step.type == "show_actor":
        lines.append(f'{pad}snesstudio_show_actor("{quote(step.actor)}");')
    elif step.type == "set_sprite_frame":
        lines.append(f'{pad}snesstudio_set_sprite_frame("{quote(step.actor)}", "{quote(step.frame)}");')
    else:
        lines.append(f'{pad}/* Unsupported step: {step.type} */')
    return lines


def chain_body(chain) -> str:
    lines: list[str] = []
    if not chain.steps:
        lines.append("    /* Empty event chain. */")
    for step in chain.steps:
        lines.extend(emit_step(step))
    return "\n".join(lines)


def export_c(project_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    project = load_project(project_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape(default=False))
    env.filters["c_ident"] = c_ident
    env.filters["chain_body"] = chain_body
    # Note: the SNES toolchain (PVSnesLib snes_rules) compiles every .c in the
    # build dir, so we emit only the real SNES engine here — not the desktop
    # printf stub, which would clash (duplicate symbols + no printf on SNES).
    # Desktop logic testing now lives in `snes-studio play` (snesstudio/sim.py).
    files = {
        "main.c": "main.c.j2",
        "snesstudio_snes.c": "snesstudio_snes.c.j2",
        "snesstudio_runtime.h": "snesstudio_runtime.h.j2",
        "Makefile": "Makefile.j2",
        "hdr.asm": "hdr.asm.j2",
        "README.generated.md": "README.generated.md.j2",
    }
    written = []
    for name, template in files.items():
        content = env.get_template(template).render(project=project)
        target = out / name
        target.write_text(content, encoding="utf-8")
        written.append(str(target))
    # Emit converted SNES assets (4bpp tiles + BGR555 palettes) alongside the C.
    from .assets import render_assets
    from .tilemap import render_tilemaps
    a_header, a_source = render_assets(project)
    (out / "snesstudio_assets.h").write_text(a_header, encoding="utf-8")
    (out / "snesstudio_assets.c").write_text(a_source, encoding="utf-8")
    m_header, m_source = render_tilemaps(project)
    (out / "snesstudio_maps.h").write_text(m_header, encoding="utf-8")
    (out / "snesstudio_maps.c").write_text(m_source, encoding="utf-8")
    written.extend([str(out / "snesstudio_assets.h"), str(out / "snesstudio_assets.c"),
                    str(out / "snesstudio_maps.h"), str(out / "snesstudio_maps.c")])
    return {"out_dir": str(out), "files": written, "project": project.name}


def make_rom(project_path: str | Path, out_file: str | Path, skip_build: bool = False) -> dict[str, Any]:
    out_file = Path(out_file)
    build_dir = out_file.parent / "generated" / out_file.stem
    result = export_c(project_path, build_dir)
    if skip_build:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        payload = b"SNESSTUDIO_PLACEHOLDER_ROM\nThis is not a playable SNES ROM. Build with PVSnesLib.\n"
        out_file.write_bytes(payload)
        return {"rom": str(out_file), "bytes": out_file.stat().st_size, "placeholder": True, "generated": result}
    try:
        subprocess.run(["make"], cwd=build_dir, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("make not found. Install a build toolchain and PVSnesLib, or use --skip-build.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("SNES build failed. Check docs/TOOLCHAIN.md and generated build output.") from exc
    candidate = build_dir / "game.sfc"
    if not candidate.exists():
        raise RuntimeError("Build completed but game.sfc was not created. Check PVSnesLib Makefile integration.")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    candidate.replace(out_file)
    return {"rom": str(out_file), "bytes": out_file.stat().st_size, "placeholder": False, "generated": result}
