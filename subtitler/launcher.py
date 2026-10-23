"""Windows-friendly launcher for the Subtitler Gradio application."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _resource_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", _app_dir()))


def main() -> None:
    app_dir = _app_dir()
    resource_dir = _resource_dir()
    os.chdir(app_dir)

    try:
        from dotenv import load_dotenv
        load_dotenv(app_dir / ".env", override=False)
    except ImportError:  # pragma: no cover
        pass

    # Prefer bundled FFmpeg in `_ffmpeg_embedded`, then PATH.
    ffmpeg_dirs = [resource_dir / "_ffmpeg_embedded", app_dir / "_ffmpeg_embedded"]
    for directory in ffmpeg_dirs:
        if directory.is_dir():
            os.environ["PATH"] = str(directory) + os.pathsep + os.environ.get("PATH", "")

    output_dir = app_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    from app.ui import build_ui
    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)


if __name__ == "__main__":
    main()
