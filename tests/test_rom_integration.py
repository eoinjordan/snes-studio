from __future__ import annotations

from pathlib import Path
import json

from snesstudio.compiler import make_rom
from snesstudio import editor


PROJECT = Path("examples/hello-human/project.snesproj")


def test_project_mutations_flow_into_generated_rom_inputs(tmp_path):
    data = json.loads(PROJECT.read_text(encoding="utf-8"))

    # 1) Mutate gameplay-relevant data via editor APIs (same model used by UI/backend).
    data = editor.update_actor(data, "school", "player", x=42, y=99)
    data = editor.add_event_chain(data, "qa_intro", "QA Intro", {"type": "scene_start", "scene": "school"})
    data = editor.add_event_step(data, "qa_intro", {"id": "qa_text", "type": "show_text", "text": "E2E ROM text marker"})
    data = editor.add_collision(data, "school", "qa_wall", 16, 16, 32, 16)

    mutated = tmp_path / "mutated.snesproj"
    mutated.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # 2) Build via make_rom (skip-build mode still runs full codegen + asset/tilemap generation).
    rom_out = tmp_path / "qa.sfc"
    result = make_rom(mutated, rom_out, skip_build=True)
    assert rom_out.exists()
    assert result["placeholder"] is True

    generated_dir = Path(result["generated"]["out_dir"])
    main_c = (generated_dir / "main.c").read_text(encoding="utf-8")
    maps_c = (generated_dir / "snesstudio_maps.c").read_text(encoding="utf-8")

    # 3) Validate mutations are present in generated ROM inputs.
    assert 'snesstudio_place_actor("player", "Player", 42, 99, "kid");' in main_c
    assert 'snesstudio_show_text("E2E ROM text marker");' in main_c
    assert "map_school" in maps_c
