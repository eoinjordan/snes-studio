# Asset Sources

Bundled showcase/template art is embedded into the `.snesproj` files as palette-indexed sprite and scene data. The current art pass uses permissively licensed OpenGameArt packs and can be regenerated with:

```bash
pip install -e ".[art]"
python scripts/import_open_art_assets.py
```

The script downloads source packs into `build/assetpacks`, crops selected frames/tiles, quantizes them to SNES Studio sprite palettes, and writes the converted data into the bundled example/template projects. The downloaded source archives are build cache only and are not required at runtime.

## CC0 Packs

- Puny Characters by Shade: https://opengameart.org/content/puny-characters
- 16x16 Puny World Tileset by Shade: https://opengameart.org/content/16x16-puny-world-tileset
- 16x16 Puny Dungeon Tileset by Shade: https://opengameart.org/content/16x16-puny-dungeon-tileset
- Ambient Pixel Art Insects by madameberry: https://opengameart.org/content/ambient-pixel-art-insects

All four source pages list the license as CC0. Attribution is not required by the license, but the project keeps these links so future maintainers can audit and regenerate the embedded art.
