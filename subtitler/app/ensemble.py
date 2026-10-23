# SPDX-License-Identifier: AGPL-3.0-or-later
"""Combine two transcription passes: keep A, fill gaps with B, dedupe overlaps."""
from __future__ import annotations

from typing import Iterable

from .base import Segment


def _sort(segments: Iterable[Segment]) -> list[Segment]:
    return sorted(segments, key=lambda s: (float(s["start"]), float(s["end"])))


def _overlap_ratio(a: Segment, b: Segment) -> float:
    start = max(float(a["start"]), float(b["start"]))
    end = min(float(a["end"]), float(b["end"]))
    if end <= start:
        return 0.0
    inter = end - start
    total_a = max(float(a["end"]) - float(a["start"]), 1e-6)
    total_b = max(float(b["end"]) - float(b["start"]), 1e-6)
    return max(inter / total_a, inter / total_b)


def merge_passes(primary: list[Segment], secondary: list[Segment], dedupe_threshold: float = 0.6) -> list[Segment]:
    """Keep ``primary`` segments; fill gaps with non-overlapping ``secondary`` segments."""
    base = _sort(primary)
    extra = _sort(secondary)
    merged: list[Segment] = list(base)

    for cand in extra:
        if all(_overlap_ratio(cand, kept) < dedupe_threshold for kept in merged):
            merged.append(dict(cand))

    merged.sort(key=lambda s: (float(s["start"]), float(s["end"])))
    cleaned: list[Segment] = []
    last_end = 0.0
    for seg in merged:
        start = max(float(seg["start"]), last_end)
        end = float(seg["end"])
        if end <= start:
            continue
        seg = dict(seg)
        seg["start"] = start
        seg["end"] = end
        cleaned.append(seg)
        last_end = end
    return cleaned
