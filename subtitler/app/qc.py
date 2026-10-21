# SPDX-License-Identifier: AGPL-3.0-or-later
"""Subtitle readability checks and line balancing."""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class QCRules:
    max_chars_per_line: int = 42
    max_lines: int = 2
    max_cps: float = 17.0
    min_duration: float = 0.5
    max_duration: float = 7.0
    min_gap_frames: int = 2
    fps: float = 24.0

def balance_lines(text: str, max_chars: int = 42) -> str:
    words = text.split()
    if len(text) <= max_chars or len(words) < 2:
        return text
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])

def check(segments: list[dict], rules: QCRules | None = None) -> list[tuple[int, str]]:
    rules = rules or QCRules()
    issues = []
    for index, segment in enumerate(segments, 1):
        text = str(segment.get("text", "")).strip()
        lines = text.splitlines() or [text]
        duration = float(segment.get("end", 0)) - float(segment.get("start", 0))
        if len(lines) > rules.max_lines or any(len(line) > rules.max_chars_per_line for line in lines): issues.append((index, "Line length or line count exceeds limits"))
        if duration < rules.min_duration: issues.append((index, "Duration is below minimum"))
        if duration > rules.max_duration: issues.append((index, "Duration exceeds maximum"))
        if duration > 0 and len(re.sub(r"\s", "", text)) / duration > rules.max_cps: issues.append((index, "Reading speed exceeds CPS limit"))
        if index > 1 and float(segment.get("start", 0)) - float(segments[index - 2].get("end", 0)) < rules.min_gap_frames / rules.fps: issues.append((index, "Gap is below minimum"))
    return issues
