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


def test_find_local_ffmpeg_finds_bundled_onefile_binary(tmp_path):
    project_root = tmp_path / "app"
    bundle_root = tmp_path / "_MEI12345"
    ffmpeg = bundle_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    ffmpeg.parent.mkdir(parents=True)
    ffmpeg.write_text("", encoding="utf-8")

    assert find_local_ffmpeg(project_root, bundle_root) == ffmpeg
