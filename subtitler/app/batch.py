# SPDX-License-Identifier: AGPL-3.0-or-later
"""Discover video files in a directory for batch processing."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".ts", ".m4v", ".flv"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt"}


def discover_videos(directory: str | Path, recursive: bool = False) -> list[Path]:
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        return []
    pattern = "**/*" if recursive else "*"
    return sorted(
        path
        for path in directory.glob(pattern)
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def has_subtitle(video: Path, extensions: set[str] | None = None) -> bool:
    extensions = extensions or SUBTITLE_EXTENSIONS
    stem = video.with_suffix("")
    return any((stem).with_suffix(ext).exists() for ext in extensions)


def iter_videos(
    inputs: list[Path], recursive: bool = False, skip_existing: bool = False
) -> Iterator[Path]:
    for entry in inputs:
        if entry.is_dir():
            for video in discover_videos(entry, recursive=recursive):
                if skip_existing and has_subtitle(video):
                    continue
                yield video
        elif entry.is_file():
            if entry.suffix.lower() in VIDEO_EXTENSIONS:
                if skip_existing and has_subtitle(entry):
                    continue
                yield entry
