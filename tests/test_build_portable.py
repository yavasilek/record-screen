from pathlib import Path


def test_build_script_creates_versioned_onefile_release_with_bundled_ffmpeg():
    project_root = Path(__file__).resolve().parents[1]
    script = (project_root / "scripts" / "build_portable.ps1").read_text(encoding="utf-8")

    assert "RecordScreen-v$Version" in script
    assert "PyInstaller" in script
    assert "requirements-dev.txt" in script
    assert "record_screen_gui.py" in script
    assert "--onefile" in script
    assert "--add-binary $FfmpegBinary" in script
    assert 'Join-Path $ReleaseRoot "RecordScreen.exe"' in script
    assert "Compress-Archive -Path $ExePath" in script
