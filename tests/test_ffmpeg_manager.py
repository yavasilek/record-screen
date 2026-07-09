from pathlib import Path

from screen_recorder.ffmpeg_manager import find_local_ffmpeg


def test_find_local_ffmpeg_prefers_standard_project_path(tmp_path):
    ffmpeg = tmp_path / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    ffmpeg.parent.mkdir(parents=True)
    ffmpeg.write_text("", encoding="utf-8")

    assert find_local_ffmpeg(tmp_path) == ffmpeg


def test_find_local_ffmpeg_finds_nested_portable_build(tmp_path):
    ffmpeg = tmp_path / "tools" / "ffmpeg" / "ffmpeg-7.1-essentials_build" / "bin" / "ffmpeg.exe"
    ffmpeg.parent.mkdir(parents=True)
    ffmpeg.write_text("", encoding="utf-8")

    assert find_local_ffmpeg(tmp_path) == ffmpeg
