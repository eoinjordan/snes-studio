# Asset Sources

Bundled showcase/template art is embedded into the `.snesproj` files as palette-indexed sprite and scene data. The current art pass uses the OpenGameArt packs requested for the Pokemon/Zelda-style direction and can be regenerated with:

```bash
pip install -e ".[art]"
python scripts/import_open_art_assets.py
```

The script downloads source packs into `build/assetpacks`, crops selected frames/tiles, quantizes them to SNES Studio sprite palettes, and writes the converted data into the bundled example/template projects. The downloaded source archives are build cache only and are not required at runtime.

## Embedded OpenGameArt Sources

- 16xx16 Tileset (Pokemon/Zelda style:D) by Damian Gasinski aka Gassasin: https://opengameart.org/content/16xx16-tileset-pokemonzelda-styled
  License: CC-BY 3.0. Attribution requested as "Damian Gasinski aka Gassasin".
- A Battle Theme (165 BPM) by Wanwaka: https://opengameart.org/content/a-battle-theme-165-bpm
  License: CC-BY 4.0. Used as battle-music source metadata.
- Tuxemon tileset by Buch: https://opengameart.org/content/tuxemon-tileset
  License: CC-BY-SA 3.0. Attribution requested as Buch with an OGA/profile/blog link.
- Retro Tileset by Paul Barden / Damian Gasinski aka Gassasin: https://opengameart.org/content/retro-tileset
  License: CC-BY 3.0. Attribution requested for Paul Barden and Damian Gasinski aka Gassasin.
- RPGui HUD - Asset Pack by Narehop: https://opengameart.org/content/rpgui-hud-asset-pack
  License: CC-BY 4.0. Used for UI/battle-box style source.
- Tiny16 Tileset by Fuwaneko Games: https://opengameart.org/content/tiny16-tileset
  License: CC-BY 3.0. Attribution requested as Fuwaneko Games.
- Ambient Pixel Art Insects by madameberry: https://opengameart.org/content/ambient-pixel-art-insects
  License: CC0. Retained for Pocket Bugs creature sprites because the requested packs are tile/UI/music focused.

## Not Embedded

- OPMon Center by Navet56: https://opengameart.org/content/opmon-center
  Not embedded. The page lists GPL 3.0 and has public comments flagging Pokemon/trademark licensing concerns, so it is tracked only as a skipped candidate in project metadata.
