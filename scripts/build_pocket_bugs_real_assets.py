"""Build professional Pocket Bugs assets from real-world reference photos.

This script:
1) downloads real bug + garden photos from Wikimedia Commons,
2) generates polished SNES-sized scene backgrounds (256x224),
3) imports bug sprites from those photos into the project.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

import sys
sys.path.insert(0, str(ROOT))

from snesstudio.assets import sprite_from_image  # noqa: E402
from snesstudio.project import load_project, save_project  # noqa: E402


PROJECT_PATH = ROOT / "examples" / "pocket-bugs" / "project.snesproj"
WEB_PROJECT_PATH = ROOT / "web" / "public" / "examples" / "pocket-bugs.snesproj"
ASSET_ROOT = ROOT / "examples" / "pocket-bugs" / "assets"
REF_DIR = ASSET_ROOT / "reference"
GEN_DIR = ASSET_ROOT / "generated"
BG_DIR = ASSET_ROOT / "backgrounds"
SPRITE_REF_DIR = ASSET_ROOT / "sprite_refs"
LICENSES_PATH = ASSET_ROOT / "SOURCE_LICENSES.json"


def ensure_dirs() -> None:
    for d in [REF_DIR, GEN_DIR, BG_DIR, SPRITE_REF_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def commons_file_url(filename: str) -> str:
    quoted = urllib.parse.quote(filename)
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quoted}"


SOURCES = {
    "ladybug": {
        "filename": "Ladybug (6818994048).jpg",
        "license": "Public Domain (US federal work marker on Wikimedia page)",
        "page": "https://commons.wikimedia.org/wiki/File:Ladybug_(6818994048).jpg",
    },
    "beetle": {
        "filename": "Stag Beetle, Ceruchus striatus.jpg",
        "license": "CC BY 2.0 (Wikimedia file page)",
        "page": "https://commons.wikimedia.org/wiki/File:Stag_Beetle,_Ceruchus_striatus.jpg",
    },
    "mantis": {
        "filename": "Praying mantis on bamboo curtain.jpg",
        "license": "CC0 1.0 (Wikimedia file page)",
        "page": "https://commons.wikimedia.org/wiki/File:Praying_mantis_on_bamboo_curtain.jpg",
    },
    "garden_path": {
        "filename": "Low angle garden path (50411312921).jpg",
        "license": "CC BY-SA 2.0 (Wikimedia file page)",
        "page": "https://commons.wikimedia.org/wiki/File:Low_angle_garden_path_(50411312921).jpg",
    },
    "backyard_scene": {
        "filename": "Backyard Garden Scene in California.jpg",
        "license": "CC0 1.0 (Wikimedia file page)",
        "page": "https://commons.wikimedia.org/wiki/File:Backyard_Garden_Scene_in_California.jpg",
    },
}


def download_sources() -> dict[str, str]:
    downloaded: dict[str, str] = {}
    for key, meta in SOURCES.items():
        path = REF_DIR / meta["filename"]
        if not path.exists():
            req = urllib.request.Request(
                commons_file_url(meta["filename"]),
                headers={"User-Agent": "Mozilla/5.0 (compatible; SNES-Studio-AssetBuilder/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                path.write_bytes(resp.read())
        downloaded[key] = str(path)
    return downloaded


def _require_pillow():
    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except Exception as exc:
        raise RuntimeError("Pillow is required. Install with: pip install pillow") from exc
    return Image, ImageEnhance, ImageFilter


def _center_crop_to(img, w: int, h: int):
    sw, sh = img.size
    src_aspect = sw / sh
    dst_aspect = w / h
    if src_aspect > dst_aspect:
        nh = sh
        nw = int(sh * dst_aspect)
    else:
        nw = sw
        nh = int(sw / dst_aspect)
    left = (sw - nw) // 2
    top = (sh - nh) // 2
    return img.crop((left, top, left + nw, top + nh)).resize((w, h))


def _stylize_bg(src_path: Path, out_path: Path, tint: tuple[int, int, int]) -> None:
    Image, ImageEnhance, ImageFilter = _require_pillow()
    img = Image.open(src_path).convert("RGB")
    img = _center_crop_to(img, 256, 224)
    img = ImageEnhance.Color(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = img.filter(ImageFilter.SMOOTH_MORE)
    overlay = Image.new("RGB", img.size, tint)
    img = Image.blend(img, overlay, 0.12)
    img = img.quantize(colors=32, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)


def _extract_bug_portrait(src_path: Path, out_path: Path) -> None:
    Image, ImageEnhance, ImageFilter = _require_pillow()
    img = Image.open(src_path).convert("RGB")
    # Square portrait crop from center with slight sharpen for sprite readability.
    side = min(img.size)
    left = (img.size[0] - side) // 2
    top = (img.size[1] - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((160, 160), Image.Resampling.LANCZOS)
    img = ImageEnhance.Sharpness(img).enhance(1.35)
    img = img.filter(ImageFilter.DETAIL)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)


def build_backgrounds(paths: dict[str, str]) -> None:
    _stylize_bg(Path(paths["garden_path"]), BG_DIR / "pocketbugs_title.png", (96, 46, 160))
    _stylize_bg(Path(paths["backyard_scene"]), BG_DIR / "pocketbugs_garden.png", (28, 110, 56))
    _stylize_bg(Path(paths["garden_path"]), BG_DIR / "pocketbugs_patch.png", (52, 125, 40))
    _stylize_bg(Path(paths["backyard_scene"]), BG_DIR / "pocketbugs_club.png", (70, 52, 35))
    _stylize_bg(Path(paths["garden_path"]), BG_DIR / "pocketbugs_arena1.png", (40, 83, 145))
    _stylize_bg(Path(paths["backyard_scene"]), BG_DIR / "pocketbugs_arena2.png", (35, 45, 65))


def build_bug_sprite_refs(paths: dict[str, str]) -> dict[str, Path]:
    out = {
        "ladybyte": SPRITE_REF_DIR / "ladybug_ref.png",
        "beetitan": SPRITE_REF_DIR / "beetle_ref.png",
        "mantykid": SPRITE_REF_DIR / "mantis_ref.png",
    }
    _extract_bug_portrait(Path(paths["ladybug"]), out["ladybyte"])
    _extract_bug_portrait(Path(paths["beetle"]), out["beetitan"])
    _extract_bug_portrait(Path(paths["mantis"]), out["mantykid"])
    return out


def import_bug_sprites(refs: dict[str, Path]) -> None:
    project = load_project(PROJECT_PATH)
    replacements = {
        "ladybyte": ("LadyByte (photo-derived)", refs["ladybyte"], 10),
        "beetitan": ("Beetitan (photo-derived)", refs["beetitan"], 10),
        "mantykid": ("Mantykid (photo-derived)", refs["mantykid"], 10),
    }
    keep = [s for s in project.sprites if s.id not in replacements]
    for sid, (name, ref_path, colors) in replacements.items():
        keep.append(sprite_from_image(sid, name, ref_path, width=16, height=16, colors=colors))
    project.sprites = keep
    save_project(PROJECT_PATH, project, backup=True)
    save_project(WEB_PROJECT_PATH, project, backup=False)


def write_license_manifest() -> None:
    payload = {
        "notes": [
            "All references sourced from Wikimedia Commons file pages.",
            "Check each file page for exact attribution/share-alike requirements before external distribution.",
        ],
        "sources": SOURCES,
    }
    LICENSES_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    paths = download_sources()
    build_backgrounds(paths)
    refs = build_bug_sprite_refs(paths)
    import_bug_sprites(refs)
    write_license_manifest()
    print("Built Pocket Bugs real-image assets and imported bug sprites.")
    print(f"Project: {PROJECT_PATH}")
    print(f"Backgrounds: {BG_DIR}")
    print(f"Sprite references: {SPRITE_REF_DIR}")


if __name__ == "__main__":
    main()
