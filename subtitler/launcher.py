"""Windows-friendly launcher for the Subtitler Gradio application."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _app_dir() -> Path:
    """Return the directory containing the executable or source checkout."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _resource_dir() -> Path:
    """Return PyInstaller's unpacked resource directory when frozen."""
    return Path(getattr(sys, "_MEIPASS", _app_dir()))


def main() -> None:
    app_dir = _app_dir()
    resource_dir = _resource_dir()
    os.chdir(app_dir)

    # Load configuration from beside Subtitler.exe (or the source checkout).
    from dotenv import load_dotenv

    load_dotenv(app_dir / ".env", override=False)

    # Prefer a bundled ffmpeg directory, then the PyInstaller resource copy,
    # and finally whatever the user already has on PATH.
    ffmpeg_dirs = [app_dir / "ffmpeg", resource_dir / "ffmpeg"]
    for directory in ffmpeg_dirs:
        if directory.is_dir():
            os.environ["PATH"] = str(directory) + os.pathsep + os.environ.get("PATH", "")
            break

    # Keep generated files and temporary working directories beside the exe.
    output_dir = app_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SUBTITLER_OUTPUT_DIR", str(output_dir))

    from app.ui import build_ui

    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)


if __name__ == "__main__":
    main()
