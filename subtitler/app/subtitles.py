# SPDX-License-Identifier: AGPL-3.0-or-later
"""SRT rendering."""
from pathlib import Path
import pysubs2
from .qc import balance_lines

def to_srt(segments: list[dict], output: str | Path) -> Path:
    subs = pysubs2.SSAFile()
    for segment in segments:
        subs.append(pysubs2.SSAEvent(start=round(float(segment["start"]) * 1000), end=round(float(segment["end"]) * 1000), text=balance_lines(str(segment.get("text", "")))))
    output = Path(output)
    subs.save(str(output), format_="srt")
    return output
