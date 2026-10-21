# SPDX-License-Identifier: AGPL-3.0-or-later
from app.subtitles import to_srt

def test_to_srt(tmp_path):
    output = to_srt([{"start": 0, "end": 2, "text": "Hello world"}], tmp_path / "out.srt")
    assert output.exists()
    assert "Hello world" in output.read_text(encoding="utf-8")
