from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import HOTKEY, PROJECT_ROOT

SETTINGS_FILE = "RecordScreen.settings.json"
SETTINGS_PATH = PROJECT_ROOT / SETTINGS_FILE

TRAY_BEHAVIOR_NONE = "none"
TRAY_BEHAVIOR_CLOSE = "close"
TRAY_BEHAVIOR_MINIMIZE = "minimize"
TRAY_BEHAVIOR_CLOSE_AND_MINIMIZE = "close_and_minimize"

VALID_TRAY_BEHAVIORS = {
    TRAY_BEHAVIOR_NONE,
    TRAY_BEHAVIOR_CLOSE,
    TRAY_BEHAVIOR_MINIMIZE,
    TRAY_BEHAVIOR_CLOSE_AND_MINIMIZE,
}


@dataclass(frozen=True)
class AppSettings:
    hotkey: str = HOTKEY
    tray_behavior: str = TRAY_BEHAVIOR_NONE


def load_settings(path: Path = SETTINGS_PATH) -> AppSettings:
    if not path.exists():
        return AppSettings()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppSettings()

    if not isinstance(raw, dict):
        return AppSettings()

    return AppSettings(
        hotkey=_clean_hotkey(raw.get("hotkey")),
        tray_behavior=_clean_tray_behavior(raw.get("tray_behavior")),
    )


def save_settings(settings: AppSettings, path: Path = SETTINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _clean_hotkey(value: Any) -> str:
    if not isinstance(value, str):
        return HOTKEY
    hotkey = value.strip().lower()
    return hotkey or HOTKEY


def _clean_tray_behavior(value: Any) -> str:
    if not isinstance(value, str):
        return TRAY_BEHAVIOR_NONE
    return value if value in VALID_TRAY_BEHAVIORS else TRAY_BEHAVIOR_NONE
