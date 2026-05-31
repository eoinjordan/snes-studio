from __future__ import annotations

import os
import shutil
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from snesstudio.server import create_app


APP_NAME = "SNES Studio"


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base.joinpath(*parts)


def app_data_dir() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "snes-studio"


def ensure_project() -> Path:
    data = app_data_dir()
    projects = data / "projects"
    projects.mkdir(parents=True, exist_ok=True)
    target = projects / "mango-island.snesproj"
    if not target.exists():
        source = resource_path("examples", "mango-island", "project.snesproj")
        shutil.copyfile(source, target)
    return target


def free_port(start: int = 8765) -> int:
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free local port found for SNES Studio.")


def make_desktop_app(project_path: Path, static_dir: Path):
    app = create_app(str(project_path))
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="studio-ui")
    return app


def start_server(project_path: Path, static_dir: Path, port: int) -> uvicorn.Server:
    config = uvicorn.Config(
        make_desktop_app(project_path, static_dir),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return server


def launch_window(url: str, project_path: Path, server: uvicorn.Server) -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("420x220")
    root.resizable(False, False)

    tk.Label(root, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(pady=(18, 4))
    tk.Label(root, text="Local studio is running.", font=("Segoe UI", 10)).pack()
    tk.Label(root, text=url, fg="#2455bb", cursor="hand2").pack(pady=(6, 10))

    def open_studio() -> None:
        webbrowser.open(url)

    def open_folder() -> None:
        folder = project_path.parent
        if sys.platform == "win32":
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def on_close() -> None:
        server.should_exit = True
        root.destroy()

    tk.Button(root, text="Open Studio", width=22, command=open_studio).pack(pady=4)
    tk.Button(root, text="Open Project Folder", width=22, command=open_folder).pack(pady=4)
    tk.Button(root, text="Quit", width=22, command=on_close).pack(pady=(4, 10))
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(350, open_studio)

    try:
        root.mainloop()
    except Exception as exc:
        messagebox.showerror(APP_NAME, str(exc))


def main() -> int:
    try:
        project_path = ensure_project()
        static_dir = resource_path("web", "dist")
        if not static_dir.exists():
            raise RuntimeError(f"Bundled web UI not found: {static_dir}")
        os.chdir(app_data_dir())
        port = free_port()
        server = start_server(project_path, static_dir, port)
        url = f"http://127.0.0.1:{port}/"
        time.sleep(0.8)
        launch_window(url, project_path, server)
        return 0
    except Exception as exc:
        try:
            import tkinter.messagebox as messagebox

            messagebox.showerror(APP_NAME, str(exc))
        except Exception:
            print(f"{APP_NAME}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
