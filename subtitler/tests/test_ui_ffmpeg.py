# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the FFmpeg availability banner."""
from __future__ import annotations

from unittest import mock

from app.ffmpeg_check import find_ffmpeg, status_message


def test_find_ffmpeg_returns_paths_when_available():
    with mock.patch("shutil.which", return_value="/usr/bin/ffmpeg") as which_mock:
        ffmpeg, ffprobe = find_ffmpeg()
    assert ffmpeg == "/usr/bin/ffmpeg"
    assert which_mock.call_count >= 2


def test_find_ffmpeg_returns_none_when_missing(monkeypatch, tmp_path):
    import app.ffmpeg_check as fc

    # 1) Pretend shutil.which finds nothing on PATH.
    monkeypatch.setattr("shutil.which", lambda *_a, **_k: None)

    # 2) Make every candidate directory report ``is_dir() == False`` so
    #    the bundled-path fallback loop is skipped entirely.
    class _FakePath:
        def __init__(self, *args, **kwargs):
            pass

        def __truediv__(self, other):
            return self

        @property
        def parent(self):
            return self

        def resolve(self):
            return self

        def is_dir(self):
            return False

        def exists(self):
            return False

        def __fspath__(self):
            return str(tmp_path)

    monkeypatch.setattr(fc, "Path", _FakePath)

    ffmpeg, ffprobe = fc.find_ffmpeg()
    assert ffmpeg is None
    assert ffprobe is None


def test_status_message_handles_missing():
    with mock.patch("app.ffmpeg_check.find_ffmpeg", return_value=(None, None)):
        ok, msg = status_message()
    assert ok is False
    assert "FFmpeg" in msg
    assert "ffmpeg.org" in msg


def test_status_message_handles_present():
    with mock.patch("app.ffmpeg_check.find_ffmpeg", return_value=("/usr/bin/ffmpeg", "/usr/bin/ffprobe")):
        ok, msg = status_message()
    assert ok is True
    assert "ready" in msg.lower()


def test_status_message_handles_missing_ffprobe():
    with mock.patch("app.ffmpeg_check.find_ffmpeg", return_value=("/usr/bin/ffmpeg", None)):
        ok, msg = status_message()
    assert ok is False
    assert "ffprobe" in msg
