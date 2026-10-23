# SPDX-License-Identifier: AGPL-3.0-or-later
"""Japanese post-processing: hallucination filtering, merging and timing fixes."""
from __future__ import annotations


import re
from collections import Counter
from typing import Iterable

from .base import Segment

_TRAILING_PARTICLES = ("ね", "よ", "わ", "か", "な", "ぞ", "ぜ", "さ", "の", "ー")
_MUSIC_TOKENS = ("♪", "♬", "♩", "【音楽】", "[音楽]", "(音楽)", "（音楽）")
_NOISE_RE = re.compile(r"^[\sあーんー….,。!?!\?]+$")
_NGRAM_DEFAULT = 4
_LOOP_MIN_REPEATS = 3


def _is_noise(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if any(token in stripped for token in _MUSIC_TOKENS):
        return True
    return bool(_NOISE_RE.match(stripped))


def _drop_consecutive_repeats(text: str) -> str:
    if not text:
        return text
    chars: list[str] = []
    prev: str | None = None
    run = 0
    for ch in text:
        if ch == prev:
            run += 1
            if run >= 2:
                continue
        else:
            prev = ch
            run = 1
        chars.append(ch)
    return "".join(chars)


def _drop_ngram_loops(text: str, n: int = _NGRAM_DEFAULT) -> str:
    if len(text) < n * _LOOP_MIN_REPEATS:
        return text
    tokens = list(text)
    counts = Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))
    dominant, frequency = counts.most_common(1)[0]
    if frequency < _LOOP_MIN_REPEATS:
        return text
    rebuilt: list[str] = []
    i = 0
    while i < len(tokens):
        if i <= len(tokens) - n and tuple(tokens[i : i + n]) == dominant:
            i += n
            continue
        rebuilt.append(tokens[i])
        i += 1
    return "".join(rebuilt)


def _filter_segment_text(text: str) -> str:
    cleaned = _drop_consecutive_repeats(text)
    cleaned = _drop_ngram_loops(cleaned)
    cleaned = cleaned.strip()
    return cleaned


def _passes_quality_gate(segment: Segment) -> bool:
    no_speech = segment.get("no_speech_prob")
    avg_logprob = segment.get("avg_logprob")
    compression = segment.get("compression_ratio")
    if no_speech is not None and float(no_speech) > 0.7:
        return False
    if avg_logprob is not None and float(avg_logprob) < -1.0:
        return False
    if compression is not None and float(compression) > 2.4:
        return False
    return True


def _merge_short_segments(segments: list[Segment], min_duration: float = 1.2) -> list[Segment]:
    if not segments:
        return []
    merged: list[Segment] = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        duration = float(seg["end"]) - float(seg["start"])
        ends_with_particle = any(text.endswith(p) for p in _TRAILING_PARTICLES)
        if (
            merged
            and (duration < min_duration or ends_with_particle)
            and float(seg["start"]) - float(merged[-1]["end"]) < 0.8
        ):
            prev = merged[-1]
            prev_text = str(prev.get("text", "")).rstrip()
            prev["text"] = f"{prev_text}{text}" if not prev_text.endswith(("。", "！", "？", ".", "!", "?")) else f"{prev_text} {text}"
            prev["end"] = float(seg["end"])
        else:
            merged.append(dict(seg))
    return merged


def _clamp_durations(segments: list[Segment], min_duration: float = 0.6, max_duration: float = 8.0) -> list[Segment]:
    for seg in segments:
        duration = float(seg["end"]) - float(seg["start"])
        if duration < min_duration:
            seg["end"] = float(seg["start"]) + min_duration
        elif duration > max_duration:
            seg["end"] = float(seg["start"]) + max_duration
    return segments


def _remove_overlaps(segments: list[Segment]) -> list[Segment]:
    cleaned: list[Segment] = []
    for seg in segments:
        start = float(seg["start"])
        end = float(seg["end"])
        if cleaned and start < float(cleaned[-1]["end"]):
            start = float(cleaned[-1]["end"])
        if end <= start:
            continue
        seg["start"] = start
        seg["end"] = end
        cleaned.append(seg)
    return cleaned


def postprocess_jp(segments: Iterable[Segment]) -> list[Segment]:
    """Apply JP-aware filtering, merging and timing normalisation."""
    out: list[Segment] = []
    for seg in segments:
        text = str(seg.get("text", "")).strip()
        if not text or _is_noise(text):
            continue
        seg = dict(seg)
        seg["text"] = _filter_segment_text(text)
        if not seg["text"] or _is_noise(seg["text"]):
            continue
        if not _passes_quality_gate(seg):
            continue
        out.append(seg)
    out = _merge_short_segments(out)
    out = _clamp_durations(out)
    out = _remove_overlaps(out)
    return out
