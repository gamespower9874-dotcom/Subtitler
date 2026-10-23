# SPDX-License-Identifier: AGPL-3.0-or-later
from app.run_report import FileReport, STATUS_DONE, summarise


def test_write_and_read(tmp_path):
    report = FileReport(input_path="video.mp4")
    report.finish(status=STATUS_DONE, segment_count=10, duration_sec=42.0)
    path = report.write(tmp_path)
    assert path.exists()
    payload = path.read_text(encoding="utf-8")
    assert "video.mp4" in payload
    assert "done" in payload
    assert '"segment_count": 10' in payload


def test_summarise_counts():
    reports = [
        FileReport(input_path="a.mp4", status=STATUS_DONE, segment_count=5),
        FileReport(input_path="b.mp4", status=STATUS_DONE, segment_count=7),
    ]
    text = summarise(reports)
    assert "2 files" in text
    assert "done=2" in text
    assert "segments=12" in text
