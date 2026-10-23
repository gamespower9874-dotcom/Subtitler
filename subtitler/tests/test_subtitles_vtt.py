# SPDX-License-Identifier: AGPL-3.0-or-later
from app.subtitles import to_srt, to_vtt, write_both


def test_to_vtt(tmp_path):
    path = to_vtt([{"start": 0, "end": 2, "text": "Hello"}], tmp_path / "out.vtt")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("WEBVTT")


def test_write_both(tmp_path):
    srt, vtt = write_both([{"start": 0, "end": 2, "text": "Hello"}], tmp_path / "sub")
    assert srt.suffix == ".srt"
    assert vtt.suffix == ".vtt"


def test_to_srt_still_works(tmp_path):
    path = to_srt([{"start": 0, "end": 1, "text": "Hi"}], tmp_path / "out.srt")
    assert path.exists()
    assert "Hi" in path.read_text(encoding="utf-8")
