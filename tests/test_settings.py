import json

from screen_recorder.config import HOTKEY
from screen_recorder.settings import (
    AppSettings,
    TRAY_BEHAVIOR_CLOSE,
    TRAY_BEHAVIOR_NONE,
    load_settings,
    save_settings,
)


def test_load_settings_returns_defaults_when_file_is_missing(tmp_path):
    settings = load_settings(tmp_path / "missing.json")

    assert settings == AppSettings()


def test_save_and_load_settings_roundtrip(tmp_path):
    path = tmp_path / "RecordScreen.settings.json"
    expected = AppSettings(hotkey="ctrl+shift+f9", tray_behavior=TRAY_BEHAVIOR_CLOSE)

    save_settings(expected, path)

    assert load_settings(path) == expected


def test_load_settings_ignores_invalid_values(tmp_path):
    path = tmp_path / "RecordScreen.settings.json"
    path.write_text(json.dumps({"hotkey": "  ", "tray_behavior": "bad"}), encoding="utf-8")

    settings = load_settings(path)

    assert settings.hotkey == HOTKEY
    assert settings.tray_behavior == TRAY_BEHAVIOR_NONE
