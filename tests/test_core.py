from pathlib import Path
import json
from snesstudio.project import load_project, inventory
from snesstudio.compiler import export_c, make_rom
from snesstudio.agent import propose_patch
from snesstudio.patches import apply_patch
from snesstudio import editor
from snesstudio import assets
from snesstudio import tilemap

PROJECT = Path('examples/hello-human/project.snesproj')


def test_tile_entry_encoding():
    assert tilemap.tile_entry(3) == 3
    assert tilemap.tile_entry(3, palette=2) == 3 | (2 << 10)
    assert tilemap.tile_entry(1, hflip=True, vflip=True) == 1 | (1 << 14) | (1 << 15)


def test_scene_tilemap_borders_and_collision():
    project = load_project(PROJECT)
    scene = project.scenes[0]
    grid = tilemap.scene_tilemap(scene)
    assert len(grid) == tilemap.MAP_W * tilemap.MAP_H
    wall = tilemap.tile_entry(tilemap.BG_WALL)
    # corners are wall
    assert grid[0] == wall
    assert grid[tilemap.MAP_W - 1] == wall
    # interior near the floor collision rect (x0,y192,w256,h32 -> bottom rows) is wall
    bottom_row = (192 // tilemap.TILE_PX)
    assert grid[bottom_row * tilemap.MAP_W + 5] == wall


def test_render_tilemaps_emits_maps_and_bg(tmp_path):
    result = tilemap.export_tilemaps(PROJECT, tmp_path)
    header = (tmp_path / 'snesstudio_maps.h').read_text()
    source = (tmp_path / 'snesstudio_maps.c').read_text()
    assert 'gfx_bgtiles' in header and 'pal_bg' in header
    assert 'map_school' in source
    assert len(result['scenes']) == len(load_project(PROJECT).scenes)


def test_hex_to_bgr555():
    assert assets.hex_to_bgr555('#000000') == 0
    assert assets.hex_to_bgr555('#ffffff') == 0x7fff
    # pure red -> low 5 bits, pure blue -> high 5 bits
    assert assets.hex_to_bgr555('#ff0000') == 0x001f
    assert assets.hex_to_bgr555('#0000ff') == 0x7c00
    assert assets.hex_to_bgr555('#fff') == 0x7fff  # shorthand expands


def test_frame_to_tiles_4bpp_layout():
    # 8x8 tile, top-left pixel = palette index 1 -> only bitplane 0 sets bit 7 of row 0
    pixels = [0] * 64
    pixels[0] = 1
    tile = assets.frame_to_tiles(pixels, 8, 8)
    assert len(tile) == assets.BYTES_PER_TILE
    assert tile[0] == 0x80   # bitplane0, row0, leftmost pixel
    assert tile[1] == 0x00   # bitplane1 unset for index 1
    assert all(b == 0 for b in tile[2:])
    # index 3 sets both low bitplanes
    pixels[0] = 3
    tile = assets.frame_to_tiles(pixels, 8, 8)
    assert tile[0] == 0x80 and tile[1] == 0x80


def test_sprite_assets_emit_expected_tiles_and_assets_roundtrip(tmp_path):
    result = assets.export_assets(PROJECT, tmp_path)
    header = (tmp_path / 'snesstudio_assets.h').read_text()
    source = (tmp_path / 'snesstudio_assets.c').read_text()
    robot = next(s for s in load_project(PROJECT).sprites if s.id == 'robot')
    expected_tiles = ((robot.width + 7) // 8) * ((robot.height + 7) // 8)
    assert f'GFX_ROBOT_TILES_PER_FRAME {expected_tiles}' in header
    assert 'gfx_robot_tiles' in source and 'pal_robot' in source
    sp = assets.sprite_assets(robot)
    assert sp['tiles_per_frame'] == expected_tiles
    assert len(sp['frames'][0]['tiles']) == expected_tiles * assets.BYTES_PER_TILE

def test_example_sprites_convert_to_visible_tiles():
    # The kid and robot example sprites carry real pixel art, so their converted
    # 4bpp tiles must contain non-transparent (non-zero) bytes — i.e. a player the
    # generated ROM can actually render, not an empty/invisible sprite.
    project = load_project(PROJECT)
    for sprite_id in ("kid", "robot"):
        sprite = next(s for s in project.sprites if s.id == sprite_id)
        conv = assets.sprite_assets(sprite)
        tiles = b"".join(f["tiles"] for f in conv["frames"])
        assert any(b != 0 for b in tiles), f"{sprite_id} converted to all-transparent tiles"


def test_poachermon_launch_template_is_complete_and_converts():
    # Poachermon is the flagship launch-template game; it must validate, carry its
    # full safari cast, and convert every creature sprite to visible 4bpp tiles.
    poach = Path('examples/poachermon/project.snesproj')
    project = load_project(poach)
    assert project.name == 'Poachermon'
    inv = inventory(project)
    assert inv['scene_count'] == 5 and inv['event_chain_count'] >= 14
    # First scene is the title screen with a scene_start intro chain.
    assert project.scenes[0].id == 'title'
    assert any(c.id == 'title_intro' and c.trigger and c.trigger.type == 'scene_start'
               for c in project.eventChains)
    for sprite_id in ('ranger', 'poacher', 'elephant', 'rhino', 'lioncub', 'bird'):
        sprite = next(s for s in project.sprites if s.id == sprite_id)
        tiles = b"".join(f["tiles"] for f in assets.sprite_assets(sprite)["frames"])
        assert any(b != 0 for b in tiles), f"{sprite_id} converted to empty tiles"
    # The web UI ships the same file as its bundled default project.
    web_copy = Path('web/public/examples/poachermon.snesproj')
    assert json.loads(web_copy.read_text()) == json.loads(poach.read_text())


def test_toolchain_path_normalization():
    # PVSNESLIB_HOME must be Unix-style for snes_rules even on Windows; the
    # detector must round-trip Windows <-> /c/ paths and report a status dict.
    from snesstudio import toolchain
    assert toolchain._unixify(r"C:\pvsneslib-install\pvsneslib") == "/c/pvsneslib-install/pvsneslib"
    assert toolchain._unixify("/opt/pvsneslib") == "/opt/pvsneslib"
    st = toolchain.status()
    assert set(st) >= {"pvsneslib_home", "pvsneslib_home_unix", "make", "ready"}
    assert isinstance(st["ready"], bool)


def test_poachermon_plays_through_to_a_win():
    # The desktop simulator must run the launch template end to end: visit every
    # scene in order and reach the win state (a Poachermon rescued, poacher caught).
    from snesstudio import sim
    run = sim.play_from_file('examples/poachermon/project.snesproj')
    assert run.scenes_visited == ['title', 'station', 'savannah', 'chase', 'rescue']
    assert run.variables.get('rescued') == 1
    assert run.flags.get('poacher_caught') is True
    text = run.text()
    assert "Gotta Save 'Em All!" in text
    assert "The Throttle of Justice" in text  # final beat reached


def test_mango_island_demake_plays_and_exports_runtime_hooks(tmp_path):
    from snesstudio import sim

    project_path = Path('examples/mango-island/project.snesproj')
    run = sim.play_from_file(project_path)
    assert run.scenes_visited == ['dock', 'tavern', 'jungle', 'cave', 'vault']
    assert run.flags.get('treasure_found') is True
    assert run.variables.get('score') == 100
    assert "golden mango" in run.text()

    out = tmp_path / 'mango'
    export_c(project_path, out)
    main_c = (out / 'main.c').read_text()
    runtime_h = (out / 'snesstudio_runtime.h').read_text()
    assert 'void snesstudio_on_action(void)' in main_c
    assert 'void snesstudio_on_step(void)' in main_c
    assert 'load_scene("tavern");' in main_c
    assert 'snesstudio_set_variable("score", 100);' in main_c
    assert 'int snesstudio_player_near' in runtime_h


def test_project_loads_and_inventory():
    project = load_project(PROJECT)
    inv = inventory(project)
    assert inv['scene_count'] >= 3
    assert inv['actor_count'] >= 3
    assert inv['event_chain_count'] >= 2


def test_editor_adds_scene_actor_chain_step_without_mutating():
    original = json.loads(PROJECT.read_text())
    next_data = editor.add_scene(original, 'lab', 'Robot Lab')
    next_data = editor.add_actor(next_data, 'lab', 'mentor', 'Mentor Bot', 80, 120, 'robot')
    next_data = editor.add_event_chain(next_data, 'mentor_intro', 'Mentor Intro', {'type': 'actor_interact', 'actor': 'mentor'})
    next_data = editor.add_event_step(next_data, 'mentor_intro', {'id': 'hello', 'type': 'show_text', 'text': 'Welcome.'})
    assert len(original['scenes']) == 3
    assert any(s['id'] == 'lab' for s in next_data['scenes'])
    assert any(c['id'] == 'mentor_intro' for c in next_data['eventChains'])


def test_editor_sprite_paint_roundtrip_and_delete_step():
    original = json.loads(PROJECT.read_text())
    area = 16 * 16
    pixels = [0] * area
    pixels[0] = 2
    next_data = editor.update_sprite(original, 'robot', {
        'name': 'Robot', 'width': 16, 'height': 16,
        'palette': ['#000000', '#334155', '#67e8f9', '#e2e8f0'],
        'frames': [{'id': 'idle_0', 'name': 'Idle', 'pixels': pixels}],
    })
    robot = next((s for s in next_data['sprites'] if s['id'] == 'robot'), None)
    assert robot is not None
    assert robot['frames'][0]['pixels'][0] == 2
    # original is untouched
    assert original['sprites'][0]['frames'][0]['pixels'] != pixels

    chain = next_data['eventChains'][0]
    with_step = editor.add_event_step(next_data, chain['id'], {'id': 'tmp_step', 'type': 'show_text', 'text': 'hi'})
    pruned = editor.delete_event_step(with_step, chain['id'], 'tmp_step')
    pruned_chain = next(c for c in pruned['eventChains'] if c['id'] == chain['id'])
    assert all(s['id'] != 'tmp_step' for s in pruned_chain['steps'])


def test_editor_add_sprite_roundtrip_and_converts_to_assets():
    original = json.loads(PROJECT.read_text())
    pixels = [0] * (8 * 8)
    pixels[0] = 1
    next_data = editor.add_sprite(original, {
        'id': 'qa_sprite',
        'name': 'QA Sprite',
        'width': 8,
        'height': 8,
        'palette': ['#000000', '#ffffff', '#67e8f9', '#ef4444'],
        'frames': [{'id': 'idle_0', 'name': 'Idle', 'pixels': pixels}],
    })
    sprite = next(s for s in next_data['sprites'] if s['id'] == 'qa_sprite')
    converted = assets.sprite_assets(sprite)
    assert converted['frames'][0]['tiles'][0] == 0x80
    assert all(s['id'] != 'qa_sprite' for s in original['sprites'])


def test_agent_patch_applies():
    data = json.loads(PROJECT.read_text())
    patch = propose_patch(load_project(PROJECT), 'Add a friendly robot who gives a hint')
    next_data = apply_patch(data, patch)
    assert any(c['id'] == 'robot_hint_chain' for c in next_data['eventChains'])


def test_export_c_and_placeholder_rom(tmp_path):
    out = tmp_path / 'generated'
    result = export_c(PROJECT, out)
    assert (out / 'main.c').exists()
    assert any('main.c' in f for f in result['files'])
    rom = tmp_path / 'game.sfc'
    rom_result = make_rom(PROJECT, rom, skip_build=True)
    assert rom.exists()
    assert rom_result['placeholder'] is True


def test_tiled_scene_export_and_collision():
    """Tile-painted scenes export real 8x8 tiles, a 32x32 map and solid collision."""
    project = load_project(PROJECT)
    ts = tilemap.load_bg_tileset("overworld")
    ids = [t["id"] for t in ts["tiles"]]
    grass, tree = ids.index("grass"), ids.index("tree")
    scene = project.scenes[0]
    cells = [grass] * (tilemap.TILE_COLS * tilemap.TILE_ROWS)
    cells[0] = tree  # solid metatile in the top-left
    scene.tilemap = cells
    scene.tileset = "overworld"

    assert tilemap.scene_is_tiled(scene)
    bank, meta = tilemap.build_real_bank(ts)
    assert len(bank) > 0 and len(meta) == len(ts["tiles"])
    words, col = tilemap.tiled_map_and_collision(scene, ts, meta)
    assert len(words) == tilemap.MAP_W * tilemap.MAP_H
    # the tree metatile occupies the top-left 2x2 of 8x8 cells and is solid
    for dy in (0, 1):
        for dx in (0, 1):
            assert col[dy * tilemap.MAP_W + dx] == 1
    # grass is walkable
    assert col[tilemap.MAP_W * 2 + 2] == 0
    # full project render includes flat tiles (16) + real tiles, and the scene map
    header, source = tilemap.render_tilemaps(project)
    assert "[tiled]" in header
    assert f"map_{__import__('snesstudio.compiler', fromlist=['c_ident']).c_ident(scene.id)}" in header
