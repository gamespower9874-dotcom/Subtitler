# SPDX-License-Identifier: AGPL-3.0-or-later
"""SRT / VTT rendering."""
from pathlib import Path

import pysubs2

from .qc import balance_lines

FORMAT_SRT = "srt"
FORMAT_VTT = "vtt"


def _to_ssa(segments: list[dict]) -> pysubs2.SSAFile:
    subs = pysubs2.SSAFile()
    for segment in segments:
        subs.append(
            pysubs2.SSAEvent(
                start=round(float(segment["start"]) * 1000),
                end=round(float(segment["end"]) * 1000),
                text=balance_lines(str(segment.get("text", ""))),
            )
        )
    return subs


def to_srt(segments: list[dict], output: str | Path) -> Path:
    output = Path(output)
    _to_ssa(segments).save(str(output), format_="srt")
    return output


def to_vtt(segments: list[dict], output: str | Path) -> Path:
    output = Path(output)
    _to_ssa(segments).save(str(output), format_="vtt")
    return output


def write(segments: list[dict], output: str | Path, format_: str = FORMAT_SRT) -> Path:
    fmt = format_.lower()
    if fmt == "srt":
        return to_srt(segments, output)
    if fmt == "vtt":
        return to_vtt(segments, output)
    raise ValueError(f"Unsupported subtitle format: {format_!r}")


def write_both(segments: list[dict], base_path: str | Path) -> tuple[Path, Path]:
    base = Path(base_path).with_suffix("")
    srt = to_srt(segments, base.with_suffix(".srt"))
    vtt = to_vtt(segments, base.with_suffix(".vtt"))
    return srt, vtt
