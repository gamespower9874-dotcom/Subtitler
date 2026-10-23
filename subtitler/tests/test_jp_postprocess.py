# SPDX-License-Identifier: AGPL-3.0-or-later
from app.jp_postprocess import postprocess_jp


def test_drops_noise_and_music():
    segs = [
        {"start": 0, "end": 1, "text": "あー"},
        {"start": 1, "end": 2, "text": "♪音楽♪"},
        {"start": 2, "end": 4, "text": "こんにちは皆さん"},
    ]
    out = postprocess_jp(segs)
    assert len(out) == 1
    assert "こんにちは" in out[0]["text"]


def test_filters_consecutive_repeats():
    segs = [{"start": 0, "end": 2, "text": "すごいすごいすごいすごい"}]
    out = postprocess_jp(segs)
    assert len(out) == 1
    assert "すごいすごいすごい" not in out[0]["text"]


def test_merges_short_segments_on_particle():
    segs = [
        {"start": 0, "end": 0.5, "text": "ほんとに"},
        {"start": 0.6, "end": 1.2, "text": "すごいね"},
    ]
    out = postprocess_jp(segs)
    assert len(out) == 1
    assert "すごいね" in out[0]["text"]


def test_quality_gate_filters_low_logprob():
    segs = [
        {"start": 0, "end": 1, "text": "普通に聞こえる", "avg_logprob": -0.2},
        {"start": 1, "end": 2, "text": "多分誤認識", "avg_logprob": -2.0},
    ]
    out = postprocess_jp(segs)
    assert len(out) == 1
    assert out[0]["text"].startswith("普通")
