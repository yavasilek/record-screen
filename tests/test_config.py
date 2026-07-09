from pathlib import Path

from screen_recorder import config


def test_default_paths_are_project_local():
    assert config.PROJECT_ROOT == Path(__file__).resolve().parents[1]
    assert config.RECORDINGS_DIR == config.PROJECT_ROOT / "recordings"
    assert config.TOOLS_DIR == config.PROJECT_ROOT / "tools"


def test_detect_project_root_uses_executable_parent_when_frozen():
    executable = Path("C:/portable/RecordScreen/RecordScreen.exe")

    assert config.detect_project_root(frozen=True, executable=executable) == executable.parent


def test_default_recording_settings():
    assert config.HOTKEY == "ctrl+alt+shift+r"
    assert config.DEFAULT_FPS == 20
    assert config.MIN_REGION_SIZE == 20
