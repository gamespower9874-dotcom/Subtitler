# SPDX-License-Identifier: AGPL-3.0-or-later


from app.batch import discover_videos, has_subtitle, iter_videos


def test_discover_videos_filters_extensions(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"")
    (tmp_path / "b.txt").write_text("nope")
    (tmp_path / "c.mkv").write_bytes(b"")
    found = discover_videos(tmp_path)
    names = {p.name for p in found}
    assert names == {"a.mp4", "c.mkv"}


def test_discover_videos_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.mp4").write_bytes(b"")
    assert any(p.name == "deep.mp4" for p in discover_videos(tmp_path, recursive=True))


def test_iter_videos_skip_existing(tmp_path):
    video = tmp_path / "movie.mp4"
    video.write_bytes(b"")
    (video.with_suffix(".srt")).write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n")
    assert list(iter_videos([video], skip_existing=True)) == []
    assert list(iter_videos([video], skip_existing=False)) == [video]


def test_has_subtitle(tmp_path):
    video = tmp_path / "movie.mp4"
    video.write_bytes(b"")
    assert not has_subtitle(video)
    (video.with_suffix(".vtt")).write_text("WEBVTT\n")
    assert has_subtitle(video)
