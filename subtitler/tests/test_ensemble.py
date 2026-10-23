# SPDX-License-Identifier: AGPL-3.0-or-later
from app.ensemble import merge_passes


def test_merges_gap_segments():
    a = [{"start": 0.0, "end": 1.0, "text": "こんにちは"}]
    b = [{"start": 2.0, "end": 3.0, "text": "さようなら"}]
    out = merge_passes(a, b)
    assert len(out) == 2
    assert [seg["text"] for seg in out] == ["こんにちは", "さようなら"]


def test_dedupes_overlapping_segments():
    a = [{"start": 0.0, "end": 2.0, "text": "こんにちは"}]
    b = [{"start": 0.2, "end": 2.1, "text": "こんにちは"}]
    out = merge_passes(a, b)
    assert len(out) == 1


def test_empty_inputs():
    assert merge_passes([], []) == []
