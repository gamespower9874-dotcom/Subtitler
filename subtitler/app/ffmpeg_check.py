# SPDX-License-Identifier: AGPL-3.0-or-later
"""FFmpeg and FFprobe availability check."""
from __future__ import annotations

import shutil
from pathlib import Path


# Optional bundled ffmpeg shipped inside ``_ffmpeg_embedded`` next to the
# app folder (frozen builds) or alongside the source tree. ``None`` means
# the user must rely on ``PATH``.
def find_ffmpeg() -> tuple[str | None, str | None]:
    """Return ``(ffmpeg_path, ffprobe_path)`` or ``(None, None)`` when missing.

    The lookup tries ``shutil.which`` first, then an optional bundled
    directory named ``_ffmpeg_embedded`` next to the project root.
    """
    candidates: list[Path] = []
    here = Path(__file__).resolve().parent
    candidates.append(here.parent / "_ffmpeg_embedded")
    candidates.append(here)

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    for directory in candidates:
        if not directory.is_dir():
            continue
        cand = directory / "ffmpeg"
        if ffmpeg is None and cand.exists():
            ffmpeg = str(cand)
        cand = directory / "ffprobe"
        if ffprobe is None and cand.exists():
            ffprobe = str(cand)
    return ffmpeg, ffprobe


def status_message() -> tuple[bool, str]:
    """Return a user-friendly (ok, message) pair for the UI banner."""
    ffmpeg, ffprobe = find_ffmpeg()
    if ffmpeg and ffprobe:
        return True, f"FFmpeg ready ({ffmpeg})"
    if ffmpeg and not ffprobe:
        return False, (
            "FFmpeg was found but ffprobe is missing. "
            "Install FFmpeg (with ffprobe) from https://ffmpeg.org and make "
            "sure both binaries are on your PATH, or drop them into the "
            "`_ffmpeg_embedded` folder next to the application."
        )
    return False, (
        "FFmpeg was not found on this machine. The pipeline cannot extract "
        "audio or read video metadata without it. Install FFmpeg (https://ffmpeg.org) "
        "and ensure `ffmpeg` and `ffprobe` are on your PATH, or drop the "
        "binaries into the `_ffmpeg_embedded` folder next to the application. "
        "You can still browse the UI but transcriptions will fail."
    )
