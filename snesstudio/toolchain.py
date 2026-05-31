"""Locate and configure the PVSnesLib build toolchain automatically.

The offline app and CLI use this so real ROM builds work without the user
hand-setting environment variables. It finds PVSnesLib + `make`, normalises
PVSNESLIB_HOME to the Unix-style path snes_rules requires (even on Windows),
and returns a ready-to-use subprocess environment.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


def _app_data() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "SNES Studio"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "SNES Studio"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "snes-studio"


def _to_real_path(p: str | Path) -> Path:
    """Accept a Windows or Unix-style ('/c/...') path and return a real Path."""
    s = str(p)
    m = re.match(r"^/([a-zA-Z])/(.*)$", s)
    if m and sys.platform == "win32":
        return Path(f"{m.group(1).upper()}:/{m.group(2)}")
    return Path(s)


def _unixify(p: str | Path) -> str:
    """PVSNESLIB_HOME must be Unix-style for snes_rules, even on Windows."""
    s = str(p).replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/(.*)$", s)
    if m:
        return f"/{m.group(1).lower()}/{m.group(2)}"
    return s


def _is_pvsneslib(home: Path) -> bool:
    return (home / "devkitsnes" / "snes_rules").exists()


def find_pvsneslib() -> Path | None:
    candidates: list[Path] = []
    env = os.environ.get("PVSNESLIB_HOME")
    if env:
        candidates.append(_to_real_path(env))
    candidates += [
        _app_data() / "pvsneslib",                 # bundled/installed by the desktop app
        Path("C:/pvsneslib-install/pvsneslib"),
        Path("C:/pvsneslib"),
        Path("C:/devkitPro/pvsneslib"),
        Path.home() / "pvsneslib",
        Path("/opt/pvsneslib"),
        Path("/usr/local/pvsneslib"),
    ]
    for c in candidates:
        try:
            if c and _is_pvsneslib(c):
                return c.resolve()
        except OSError:
            continue
    return None


def find_make() -> str | None:
    found = shutil.which("make")
    if found:
        return found
    for p in (
        Path("C:/devkitPro/msys2/usr/bin/make.exe"),
        Path("C:/msys64/usr/bin/make.exe"),
        Path("C:/msys32/usr/bin/make.exe"),
    ):
        if p.exists():
            return str(p)
    return None


def status() -> dict[str, Any]:
    home = find_pvsneslib()
    make = find_make()
    return {
        "pvsneslib_home": str(home) if home else None,
        "pvsneslib_home_unix": _unixify(home) if home else None,
        "make": make,
        "ready": bool(home and make),
    }


def build_env() -> tuple[dict[str, str], str] | None:
    """Return (env, make_exe) ready for `subprocess.run`, or None if unavailable."""
    home = find_pvsneslib()
    make = find_make()
    if not home or not make:
        return None
    env = dict(os.environ)
    env["PVSNESLIB_HOME"] = _unixify(home)
    extra = [
        str(home / "devkitsnes" / "bin"),
        str(home / "devkitsnes" / "tools"),
        str(Path(make).parent),
    ]
    env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "")])
    return env, make
