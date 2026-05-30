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


def test_16x16_sprite_emits_four_tiles_and_assets_roundtrip(tmp_path):
    result = assets.export_assets(PROJECT, tmp_path)
    header = (tmp_path / 'snesstudio_assets.h').read_text()
    source = (tmp_path / 'snesstudio_assets.c').read_text()
    assert 'GFX_ROBOT_TILES_PER_FRAME 4' in header   # 16x16 -> 4 tiles
    assert 'gfx_robot_tiles' in source and 'pal_robot' in source
    sp = assets.sprite_assets(next(s for s in [{'id': 'robot', 'name': 'Robot', 'width': 16, 'height': 16,
        'palette': ['#000000', '#334155', '#67e8f9', '#e2e8f0'], 'frames': []}]))
    assert sp['tiles_per_frame'] == 4
    assert len(sp['frames'][0]['tiles']) == 4 * assets.BYTES_PER_TILE

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
    assert inv['scene_count'] == 4 and inv['event_chain_count'] >= 12
    for sprite_id in ('ranger', 'poacher', 'elephant', 'rhino', 'lioncub', 'bird'):
        sprite = next(s for s in project.sprites if s.id == sprite_id)
        tiles = b"".join(f["tiles"] for f in assets.sprite_assets(sprite)["frames"])
        assert any(b != 0 for b in tiles), f"{sprite_id} converted to empty tiles"
    # The web UI ships the same file as its bundled default project.
    web_copy = Path('web/public/examples/poachermon.snesproj')
    assert json.loads(web_copy.read_text()) == json.loads(poach.read_text())


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
    assert json.loads(PROJECT.read_text())['sprites'][0]['frames'][0]['pixels'] == []

    chain = next_data['eventChains'][0]
    with_step = editor.add_event_step(next_data, chain['id'], {'id': 'tmp_step', 'type': 'show_text', 'text': 'hi'})
    pruned = editor.delete_event_step(with_step, chain['id'], 'tmp_step')
    pruned_chain = next(c for c in pruned['eventChains'] if c['id'] == chain['id'])
    assert all(s['id'] != 'tmp_step' for s in pruned_chain['steps'])


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
